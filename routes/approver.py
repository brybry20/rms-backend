import json
import cloudinary.uploader
from flask import request, jsonify
from database.db import get_db_connection
from models.rma import RMA
from bson import ObjectId
from datetime import date, datetime

def register_approver_routes(app):
    
    @app.route('/api/approver/pending', methods=['GET'])
    def get_pending_approvals():
        rmas = RMA.get_pending_for_approver()
        return jsonify({'rmas': rmas}), 200
    
    @app.route('/api/approver/history', methods=['GET'])
    def get_approval_history():
        db = get_db_connection()
        rmas = list(db.rma_requests.find({"status": {"$in": ["approved", "rejected", "completed"]}}).sort("updated_at", -1))
        
        result = []
        for rma in rmas:
            rma['id'] = str(rma.pop('_id'))
            result.append(rma)
        
        return jsonify({'rmas': result}), 200
    
    @app.route('/api/approver/approve/<rma_id>', methods=['PUT'])
    def approve_rma(rma_id):
        data = request.form.to_dict()
        files = request.files.getlist('approver_attachments')
        
        attachment_names_json = data.get('attachment_names', '[]')
        try:
            attachment_names = json.loads(attachment_names_json)
        except:
            attachment_names = []
        
        approved_by = data.get('approved_by')
        approved_date = data.get('approved_date', str(date.today()))
        approved_with = data.get('approved_with')
        replacement_order_no = data.get('replacement_order_no')
        closed_date = data.get('closed_date')
        approver_comments = data.get('approver_comments')
        
        if not approved_by:
            return jsonify({'error': 'approved_by is required'}), 400
        if not closed_date:
            return jsonify({'error': 'closed_date is required'}), 400
        
        # Upload files to Cloudinary
        attachment_urls = []
        for idx, file in enumerate(files):
            if file and file.filename:
                original_name = attachment_names[idx] if idx < len(attachment_names) else file.filename
                try:
                    upload_result = cloudinary.uploader.upload(
                        file,
                        folder=f"approver_attachments/{rma_id}",
                        resource_type="auto",
                        use_filename=True,
                        unique_filename=False,
                        filename_override=original_name
                    )
                    attachment_urls.append({
                        'url': upload_result['secure_url'],
                        'public_id': upload_result['public_id'],
                        'resource_type': upload_result['resource_type'],
                        'format': upload_result.get('format', 'unknown'),
                        'bytes': upload_result.get('bytes', 0),
                        'original_filename': original_name,
                        'filename': original_name
                    })
                except Exception as e:
                    print(f"Upload error: {e}")
        
        approve_data = {
            'approved_by': approved_by,
            'approved_date': approved_date,
            'approved_with': approved_with,
            'replacement_order_no': replacement_order_no,
            'closed_date': closed_date,
            'approver_comments': approver_comments,
            'approver_attachments': attachment_urls
        }
        
        result = RMA.approve(rma_id, approve_data)
        
        if result['success']:
            return jsonify({'message': 'RMA approved successfully!', 'status': 'approved'}), 200
        else:
            return jsonify({'error': result['error']}), 400
    
    @app.route('/api/approver/reject/<rma_id>', methods=['PUT'])
    def reject_approval(rma_id):
        data = request.get_json()
        
        approved_by = data.get('approved_by')
        approver_comments = data.get('approver_comments')
        
        if not approved_by:
            return jsonify({'error': 'approved_by is required'}), 400
        
        reject_data = {
            'approved_by': approved_by,
            'approver_comments': approver_comments
        }
        
        result = RMA.reject(rma_id, reject_data, 'approver')
        
        if result['success']:
            return jsonify({'message': 'RMA rejected!', 'status': 'rejected'}), 200
        else:
            return jsonify({'error': result['error']}), 400
    
    @app.route('/api/approver/update_approved/<rma_id>', methods=['PUT'])
    def update_approved_rma(rma_id):
        data = request.form.to_dict()
        files = request.files.getlist('approver_attachments')
        
        attachment_names_json = data.get('attachment_names', '[]')
        try:
            attachment_names = json.loads(attachment_names_json)
        except:
            attachment_names = []
        
        approved_by = data.get('approved_by')
        approved_date = data.get('approved_date')
        approved_with = data.get('approved_with')
        replacement_order_no = data.get('replacement_order_no')
        closed_date = data.get('closed_date')
        approver_comments = data.get('approver_comments')
        
        db = get_db_connection()
        
        rma = db.rma_requests.find_one({"_id": ObjectId(rma_id)})
        if not rma:
            return jsonify({'error': 'RMA not found'}), 404
        
        # Upload new attachments if any
        if files:
            attachment_urls = []
            for idx, file in enumerate(files):
                if file and file.filename:
                    original_name = attachment_names[idx] if idx < len(attachment_names) else file.filename
                    try:
                        upload_result = cloudinary.uploader.upload(
                            file,
                            folder=f"approver_attachments/{rma_id}",
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
            attachments_json = rma.get('approver_attachments', [])
        
        result = db.rma_requests.update_one(
            {"_id": ObjectId(rma_id)},
            {"$set": {
                "approved_by": approved_by,
                "approved_date": approved_date,
                "approved_with": approved_with,
                "replacement_order_no": replacement_order_no,
                "closed_date": closed_date,
                "approver_comments": approver_comments,
                "approver_attachments": attachments_json,
                "updated_at": datetime.now()
            }}
        )
        
        if result.modified_count > 0:
            return jsonify({'message': 'Approval details updated successfully!'}), 200
        return jsonify({'error': 'No changes made'}), 400

    @app.route('/api/approver/request-change/<rma_id>', methods=['PUT'])
    def request_change(rma_id):
        data = request.get_json()
        
        approved_by = data.get('approved_by')
        approver_comments = data.get('approver_comments')
        
        if not approved_by:
            return jsonify({'error': 'approved_by is required'}), 400
        
        db = get_db_connection()
        
        result = db.rma_requests.update_one(
            {"_id": ObjectId(rma_id), "status": "authorized"},
            {"$set": {
                "approved_by": approved_by,
                "approver_comments": approver_comments,
                "status": "pending_dealer",
                "updated_at": datetime.now()
            }}
        )
        
        if result.modified_count > 0:
            return jsonify({'message': 'Changes requested! RMA returned to dealer.', 'status': 'pending_dealer'}), 200
        return jsonify({'error': 'RMA not found or not authorized'}), 400