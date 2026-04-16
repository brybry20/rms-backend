from flask import request, jsonify
from models.user import User
from models.rma import RMA
from database.db import get_db_connection
from bson import ObjectId
from datetime import datetime

def register_admin_routes(app):
    
    @app.route('/api/admin/pending-dealers', methods=['GET'])
    def get_pending_dealers():
        dealers = User.get_pending_dealers()
        return jsonify({'dealers': dealers}), 200
    
    @app.route('/api/admin/approve-dealer/<user_id>', methods=['PUT'])
    def approve_dealer(user_id):
        result = User.approve_dealer(user_id)
        
        if result['success']:
            return jsonify({'message': 'Dealer approved successfully!'}), 200
        else:
            return jsonify({'error': result['error']}), 400
    
    @app.route('/api/admin/reject-dealer/<user_id>', methods=['DELETE'])
    def reject_dealer(user_id):
        db = get_db_connection()
        
        # Delete dealer profile and user
        db.dealer_profiles.delete_one({"user_id": user_id})
        db.users.delete_one({"_id": ObjectId(user_id), "role": "dealer"})
        
        return jsonify({'message': 'Dealer rejected and deleted successfully!'}), 200
    
    @app.route('/api/admin/all-dealers', methods=['GET'])
    def get_all_dealers():
        dealers = User.get_all_dealers()
        return jsonify({'dealers': dealers}), 200
    
    @app.route('/api/admin/all-rma', methods=['GET'])
    def get_all_rma():
        rmas = RMA.get_all()
        return jsonify({'rmas': rmas}), 200
    
    @app.route('/api/admin/rma/<rma_id>', methods=['GET'])
    def get_rma_details(rma_id):
        rma = RMA.get_by_id(rma_id)
        if rma:
            return jsonify({'rma': rma}), 200
        else:
            return jsonify({'error': 'RMA not found'}), 404
    
    @app.route('/api/admin/rma/<rma_id>', methods=['PUT'])
    def update_admin_rma(rma_id):
        data = request.get_json()
        db = get_db_connection()
        
        allowed_fields = [
            'status', 'return_type', 'reason_for_return', 'warranty',
            'filer_name', 'distributor_name', 'product', 'product_description',
            'work_environment', 'po_number', 'sales_invoice_number',
            'shipping_date', 'return_date', 'end_user_company', 'end_user_location',
            'end_user_industry', 'end_user_contact_person', 'problem_description',
            'dealer_comments', 'authorized_by', 'authorized_date', 'return_received_by',
            'authorizer_comments', 'approved_by', 'approved_date', 'approved_with',
            'replacement_order_no', 'closed_date', 'approver_comments'
        ]
        
        update_data = {}
        for field in allowed_fields:
            if field in data:
                if field == 'warranty':
                    update_data[field] = 1 if data[field] else 0
                else:
                    update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No fields to update'}), 400
        
        update_data['updated_at'] = datetime.now()
        
        result = db.rma_requests.update_one(
            {"_id": ObjectId(rma_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({'message': 'RMA updated successfully!'}), 200
        return jsonify({'error': 'No changes made'}), 400
    
    @app.route('/api/admin/rma/<rma_id>', methods=['DELETE'])
    def delete_admin_rma(rma_id):
        db = get_db_connection()
        
        # Get RMA to delete attachments from Cloudinary
        rma = db.rma_requests.find_one({"_id": ObjectId(rma_id)})
        if rma:
            import cloudinary.uploader
            # Delete attachments
            for att in rma.get('attachments', []):
                if att.get('public_id'):
                    try:
                        cloudinary.uploader.destroy(att['public_id'])
                    except:
                        pass
        
        result = db.rma_requests.delete_one({"_id": ObjectId(rma_id)})
        
        if result.deleted_count > 0:
            return jsonify({'message': 'RMA deleted successfully!'}), 200
        return jsonify({'error': 'RMA not found'}), 404
    
    @app.route('/api/admin/stats', methods=['GET'])
    def get_stats():
        db = get_db_connection()
        
        # Status counts
        status_counts = RMA.get_stats()
        
        # Dealer counts
        total_dealers = db.users.count_documents({"role": "dealer"})
        approved_dealers = db.dealer_profiles.count_documents({"is_approved": 1})
        pending_dealers = total_dealers - approved_dealers
        
        return jsonify({
            'status_counts': status_counts,
            'dealers': {
                'total': total_dealers,
                'approved': approved_dealers,
                'pending': pending_dealers
            }
        }), 200
    
    @app.route('/api/admin/users', methods=['GET'])
    def get_all_users():
        db = get_db_connection()
        users = list(db.users.find().sort("created_at", -1))
        
        # Serialize users
        result = []
        for user in users:
            user['id'] = str(user.pop('_id'))
            result.append(user)
        
        return jsonify({'users': result}), 200

    @app.route('/api/debug-pending', methods=['GET'])
    def debug_pending():
        db = get_db_connection()
        
        # Direct query to see what's happening
        pipeline = [
            {"$match": {"role": "dealer"}},
            {"$lookup": {
                "from": "dealer_profiles",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "profile"
            }},
            {"$unwind": {"path": "$profile", "preserveNullAndEmptyArrays": True}},
            {"$match": {"profile.is_approved": 0}}
        ]
        
        result = list(db.users.aggregate(pipeline))
        
        # Convert ObjectId to string for JSON
        for doc in result:
            doc['_id'] = str(doc['_id'])
            if doc.get('profile'):
                doc['profile']['_id'] = str(doc['profile']['_id'])
        
        return jsonify({
            'count': len(result),
            'dealers': result
        }), 200

    @app.route('/api/admin/create-user', methods=['POST'])
    def create_user():
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        email = data.get('email')
        contact_number = data.get('contact_number')
        
        if not all([username, password, role, email]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if role not in ['authorizer', 'approver']:
            return jsonify({'error': 'Invalid role. Must be authorizer or approver'}), 400
        
        result = User.create(username, password, role, email, contact_number)
        
        if result['success']:
            return jsonify({
                'message': f'{role} account created successfully!',
                'user_id': result['user_id']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400

    @app.route('/api/admin/dealer/<user_id>', methods=['PUT'])
    def update_dealer(user_id):
        data = request.get_json()
        result = User.update_dealer_profile(user_id, data)
        return jsonify({'message': 'Dealer updated successfully!'}), 200

    @app.route('/api/admin/dealer/<user_id>/change-password', methods=['PUT'])
    def change_dealer_password(user_id):
        data = request.get_json()
        new_password = data.get('new_password')
        
        if not new_password or len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        result = User.change_password(user_id, new_password)
        
        if result['success']:
            return jsonify({'message': 'Password changed successfully!'}), 200
        return jsonify({'error': result['error']}), 400