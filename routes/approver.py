from flask import request, jsonify
from database.db import get_db_connection
from datetime import date
import json
import cloudinary
import cloudinary.uploader

def register_approver_routes(app):
    
    @app.route('/api/approver/pending', methods=['GET'])
    def get_pending_approvals():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.username as dealer_name, dp.company_name,
                   au.username as authorizer_name
            FROM rma_requests r
            JOIN users u ON r.dealer_id = u.id
            JOIN dealer_profiles dp ON u.id = dp.user_id
            LEFT JOIN users au ON r.authorized_by = au.id
            WHERE r.status = 'authorized'
            ORDER BY r.authorized_date ASC
        ''')
        
        rmas = []
        for row in cursor.fetchall():
            rmas.append(dict(row))
        
        cursor.close()
        conn.close()
        
        return jsonify({'rmas': rmas}), 200
    
    @app.route('/api/approver/history', methods=['GET'])
    def get_approval_history():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.username as dealer_name, dp.company_name,
                   au.username as authorizer_name,
                   ap.username as approver_name
            FROM rma_requests r
            JOIN users u ON r.dealer_id = u.id
            JOIN dealer_profiles dp ON u.id = dp.user_id
            LEFT JOIN users au ON r.authorized_by = au.id
            LEFT JOIN users ap ON r.approved_by = ap.id
            WHERE r.status = 'approved' OR r.status = 'rejected' OR r.status = 'completed'
            ORDER BY r.updated_at DESC
        ''')
        
        rmas = []
        for row in cursor.fetchall():
            rma_dict = dict(row)
            if rma_dict.get('approver_attachments'):
                try:
                    rma_dict['approver_attachments'] = json.loads(rma_dict['approver_attachments'])
                except:
                    rma_dict['approver_attachments'] = []
            else:
                rma_dict['approver_attachments'] = []
            rmas.append(rma_dict)
        
        cursor.close()
        conn.close()
        
        return jsonify({'rmas': rmas}), 200
    
    @app.route('/api/approver/approve/<int:rma_id>', methods=['PUT'])
    def approve_rma(rma_id):
        # Handle form data with files
        data = request.form.to_dict()
        files = request.files.getlist('approver_attachments')
        
        # ✅ Kunin ang attachment_names mula sa request
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
        
        # Upload files to Cloudinary with original filename
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
                        filename_override=original_name  # ✅ panatilihin ang orihinal na pangalan
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
                    print(f"Uploaded: {original_name} -> {upload_result['secure_url']}")
                except Exception as e:
                    print(f"Upload error: {e}")
        
        attachments_json = json.dumps(attachment_urls) if attachment_urls else None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT status FROM rma_requests WHERE id = ?', (rma_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA not found'}), 404
        
        if row['status'] != 'authorized':
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA is not authorized'}), 400
        
        try:
            cursor.execute('''
                UPDATE rma_requests SET
                    approved_by = ?,
                    approved_date = ?,
                    approved_with = ?,
                    replacement_order_no = ?,
                    closed_date = ?,
                    approver_comments = ?,
                    approver_attachments = ?,
                    status = 'approved',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (approved_by, approved_date, approved_with, replacement_order_no, closed_date, approver_comments, attachments_json, rma_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'message': 'RMA approved successfully!',
                'status': 'approved'
            }), 200
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/approver/reject/<int:rma_id>', methods=['PUT'])
    def reject_approval(rma_id):
        data = request.get_json()
        
        approved_by = data.get('approved_by')
        approver_comments = data.get('approver_comments')
        
        if not approved_by:
            return jsonify({'error': 'approved_by is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT status FROM rma_requests WHERE id = ?', (rma_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA not found'}), 404
        
        if row['status'] != 'authorized':
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA is not authorized'}), 400
        
        try:
            cursor.execute('''
                UPDATE rma_requests SET
                    approved_by = ?,
                    approver_comments = ?,
                    status = 'rejected',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (approved_by, approver_comments, rma_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'message': 'RMA rejected!',
                'status': 'rejected'
            }), 200
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/approver/update_approved/<int:rma_id>', methods=['PUT'])
    def update_approved_rma(rma_id):
        """Update approval details for an already approved RMA"""
        data = request.form.to_dict()
        files = request.files.getlist('approver_attachments')
        
        # ✅ Kunin ang attachment_names para sa pag-update
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT status, approver_attachments FROM rma_requests WHERE id = ?', (rma_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA not found'}), 404
        
        # Process attachments with original filename
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
            attachments_json = json.dumps(attachment_urls) if attachment_urls else None
        else:
            attachments_json = row['approver_attachments']
        
        try:
            cursor.execute('''
                UPDATE rma_requests SET
                    approved_by = ?,
                    approved_date = ?,
                    approved_with = ?,
                    replacement_order_no = ?,
                    closed_date = ?,
                    approver_comments = ?,
                    approver_attachments = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (approved_by, approved_date, approved_with, replacement_order_no, closed_date, approver_comments, attachments_json, rma_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'message': 'Approval details updated successfully!'}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 400

    @app.route('/api/approver/request-change/<int:rma_id>', methods=['PUT'])
    def request_change(rma_id):
        data = request.get_json()
        
        approved_by = data.get('approved_by')
        approver_comments = data.get('approver_comments')
        
        if not approved_by:
            return jsonify({'error': 'approved_by is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT status FROM rma_requests WHERE id = ?', (rma_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA not found'}), 404
        
        if row['status'] != 'authorized':
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA is not authorized'}), 400
        
        try:
            cursor.execute('''
                UPDATE rma_requests SET
                    approved_by = ?,
                    approver_comments = ?,
                    status = 'pending_dealer',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (approved_by, approver_comments, rma_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'message': 'Changes requested! RMA returned to dealer.',
                'status': 'pending_dealer'
            }), 200
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 400