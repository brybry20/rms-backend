import json
import cloudinary.uploader
from flask import request, jsonify
from database.db import get_db_connection
from models.rma import RMA
from bson import ObjectId
from datetime import date, datetime

def register_authorizer_routes(app):
    
    @app.route('/api/authorizer/pending', methods=['GET'])
    def get_pending_rmas():
        rmas = RMA.get_pending_for_authorizer()
        return jsonify({'rmas': rmas}), 200

    @app.route('/api/authorizer/authorize/<rma_id>', methods=['PUT'])
    def authorize_rma(rma_id):
        data = request.form.to_dict()
        files = request.files.getlist('authorizer_attachments')
        
        attachment_names_json = data.get('attachment_names', '[]')
        try:
            attachment_names = json.loads(attachment_names_json)
        except:
            attachment_names = []
        
        authorized_by = data.get('authorized_by')
        authorized_date = data.get('authorized_date', str(date.today()))
        return_date = data.get('return_date')
        return_received_by = data.get('return_received_by')
        authorizer_comments = data.get('authorizer_comments')
        
        if not authorized_by:
            return jsonify({'error': 'authorized_by is required'}), 400
        if not return_date:
            return jsonify({'error': 'return_date is required'}), 400
        if not return_received_by:
            return jsonify({'error': 'return_received_by is required'}), 400
        
        # Upload files to Cloudinary
        attachment_urls = []
        for idx, file in enumerate(files):
            if file and file.filename:
                original_name = attachment_names[idx] if idx < len(attachment_names) else file.filename
                try:
                    upload_result = cloudinary.uploader.upload(
                        file,
                        folder=f"authorizer_attachments/{rma_id}",
                        resource_type="auto",
                        use_filename=True,
                        unique_filename=False,
                        filename_override=original_name
                    )
                    attachment_urls.append({
                        'url': upload_result['secure_url'],
                        'public_id': upload_result['public_id'],
                        'resource_type': upload_result['resource_type'],
                        'original_filename': original_name,
                        'filename': original_name
                    })
                except Exception as e:
                    print(f"Upload error: {e}")
        
        authorize_data = {
            'authorized_by': authorized_by,
            'authorized_date': authorized_date,
            'return_date': return_date,
            'return_received_by': return_received_by,
            'authorizer_comments': authorizer_comments,
            'authorizer_attachments': attachment_urls
        }
        
        result = RMA.authorize(rma_id, authorize_data)
        
        if result['success']:
            return jsonify({'message': 'RMA authorized successfully!', 'status': 'authorized'}), 200
        else:
            return jsonify({'error': result['error']}), 400

    @app.route('/api/authorizer/reject/<rma_id>', methods=['PUT'])
    def reject_rma(rma_id):
        data = request.get_json()
        authorized_by = data.get('authorized_by')
        authorizer_comments = data.get('authorizer_comments')
        
        if not authorized_by:
            return jsonify({'error': 'authorized_by is required'}), 400
        
        reject_data = {
            'authorized_by': authorized_by,
            'authorizer_comments': authorizer_comments
        }
        
        result = RMA.reject(rma_id, reject_data, 'authorizer')
        
        if result['success']:
            return jsonify({'message': 'RMA rejected!', 'status': 'rejected'}), 200
        else:
            return jsonify({'error': result['error']}), 400

    @app.route('/api/authorizer/back-to-dealer/<rma_id>', methods=['PUT'])
    def back_to_dealer(rma_id):
        data = request.get_json()
        authorized_by = data.get('authorized_by')
        authorizer_comments = data.get('authorizer_comments')
        
        if not authorized_by:
            return jsonify({'error': 'authorized_by is required'}), 400
        
        db = get_db_connection()
        
        result = db.rma_requests.update_one(
            {"_id": ObjectId(rma_id), "status": "pending_authorizer"},
            {"$set": {
                "authorized_by": authorized_by,
                "authorizer_comments": authorizer_comments,
                "status": "pending_dealer",
                "updated_at": datetime.now()
            }}
        )
        
        if result.modified_count > 0:
            return jsonify({'message': 'RMA returned to dealer for revision!', 'status': 'pending_dealer'}), 200
        return jsonify({'error': 'RMA not found or not pending for authorization'}), 400

    @app.route('/api/authorizer/history', methods=['GET'])
    def get_authorized_rmas():
        db = get_db_connection()
        rmas = list(db.rma_requests.find({"authorized_by": {"$ne": None}}).sort("authorized_date", -1))
        
        result = []
        for rma in rmas:
            rma['id'] = str(rma.pop('_id'))
            if rma.get('authorizer_attachments'):
                pass  # Keep as is
            result.append(rma)
        
        return jsonify({'rmas': result}), 200

    @app.route('/api/authorizer/update_authorized/<rma_id>', methods=['PUT'])
    def update_authorized_rma(rma_id):
        data = request.form.to_dict()
        files = request.files.getlist('authorizer_attachments')
        
        attachment_names_json = data.get('attachment_names', '[]')
        try:
            attachment_names = json.loads(attachment_names_json)
        except:
            attachment_names = []
        
        authorized_by = data.get('authorized_by')
        return_date = data.get('return_date')
        return_received_by = data.get('return_received_by')
        authorizer_comments = data.get('authorizer_comments')
        
        if not authorized_by:
            return jsonify({'error': 'Authorized By is required'}), 400
        if not return_date:
            return jsonify({'error': 'Return Date is required'}), 400
        if not return_received_by:
            return jsonify({'error': 'Return Received By is required'}), 400
        
        db = get_db_connection()
        
        # Check current status
        rma = db.rma_requests.find_one({"_id": ObjectId(rma_id)})
        if not rma:
            return jsonify({'error': 'RMA not found'}), 404
        
        if rma['status'] not in ['authorized', 'approved', 'pending_approver']:
            return jsonify({'error': 'Cannot edit - RMA status is ' + rma['status']}), 400
        
        # Upload new attachments if any
        if files:
            attachment_urls = []
            for idx, file in enumerate(files):
                if file and file.filename:
                    original_name = attachment_names[idx] if idx < len(attachment_names) else file.filename
                    try:
                        upload_result = cloudinary.uploader.upload(
                            file,
                            folder=f"authorizer_attachments/{rma_id}",
                            resource_type="auto",
                            use_filename=True,
                            unique_filename=False,
                            filename_override=original_name
                        )
                        attachment_urls.append({
                            'url': upload_result['secure_url'],
                            'public_id': upload_result['public_id'],
                            'resource_type': upload_result['resource_type'],
                            'original_filename': original_name,
                            'filename': original_name
                        })
                    except Exception as e:
                        print(f"Upload error: {e}")
            attachments_json = attachment_urls
        else:
            attachments_json = rma.get('authorizer_attachments', [])
        
        result = db.rma_requests.update_one(
            {"_id": ObjectId(rma_id)},
            {"$set": {
                "authorized_by": authorized_by,
                "return_date": return_date,
                "return_received_by": return_received_by,
                "authorizer_comments": authorizer_comments,
                "authorizer_attachments": attachments_json,
                "updated_at": datetime.now()
            }}
        )
        
        if result.modified_count > 0:
            return jsonify({'message': 'Authorization details updated successfully!'}), 200
        return jsonify({'error': 'No changes made'}), 400

    # --- Analytics routes ---
    @app.route('/api/authorizer/all-rma', methods=['GET'])
    def auth_get_all_rma():
        rmas = RMA.get_all()
        return jsonify({'rmas': rmas}), 200
    
    @app.route('/api/authorizer/stats', methods=['GET'])
    def auth_get_stats():
        status_counts = RMA.get_stats()
        return jsonify({'status_counts': status_counts}), 200
