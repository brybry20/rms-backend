import json
import cloudinary.uploader
from flask import request, jsonify
from database.db import get_db_connection
from datetime import date

def register_authorizer_routes(app):
    
    @app.route('/api/authorizer/pending', methods=['GET'])
    def get_pending_rmas():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, u.username as dealer_name, dp.company_name
            FROM rma_requests r
            JOIN users u ON r.dealer_id = u.id
            JOIN dealer_profiles dp ON u.id = dp.user_id
            WHERE r.status = 'pending_authorizer'
            ORDER BY r.created_at ASC
        ''')
        rmas = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify({'rmas': rmas}), 200

    @app.route('/api/authorizer/authorize/<int:rma_id>', methods=['PUT'])
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
        attachments_json = json.dumps(attachment_urls) if attachment_urls else None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM rma_requests WHERE id = %s', (rma_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA not found'}), 404
        if row['status'] != 'pending_authorizer':
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA is not pending for authorization'}), 400
        
        try:
            cursor.execute('''
                UPDATE rma_requests SET
                    authorized_by = %s,
                    authorized_date = %s,
                    return_date = %s,
                    return_received_by = %s,
                    authorizer_comments = %s,
                    authorizer_attachments = %s,
                    status = 'authorized',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (authorized_by, authorized_date, return_date, return_received_by,
                  authorizer_comments, attachments_json, rma_id))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'RMA authorized successfully!', 'status': 'authorized'}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 400

    @app.route('/api/authorizer/reject/<int:rma_id>', methods=['PUT'])
    def reject_rma(rma_id):
        data = request.get_json()
        authorized_by = data.get('authorized_by')
        authorizer_comments = data.get('authorizer_comments')
        if not authorized_by:
            return jsonify({'error': 'authorized_by is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM rma_requests WHERE id = %s', (rma_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA not found'}), 404
        if row['status'] != 'pending_authorizer':
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA is not pending for authorization'}), 400
        
        try:
            cursor.execute('''
                UPDATE rma_requests SET
                    authorized_by = %s,
                    authorizer_comments = %s,
                    status = 'rejected',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (authorized_by, authorizer_comments, rma_id))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'RMA rejected!', 'status': 'rejected'}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 400

    @app.route('/api/authorizer/back-to-dealer/<int:rma_id>', methods=['PUT'])
    def back_to_dealer(rma_id):
        data = request.get_json()
        authorized_by = data.get('authorized_by')
        authorizer_comments = data.get('authorizer_comments')
        if not authorized_by:
            return jsonify({'error': 'authorized_by is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM rma_requests WHERE id = %s', (rma_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA not found'}), 404
        if row['status'] != 'pending_authorizer':
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA is not pending for authorization'}), 400
        
        try:
            cursor.execute('''
                UPDATE rma_requests SET
                    authorized_by = %s,
                    authorizer_comments = %s,
                    status = 'pending_dealer',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (authorized_by, authorizer_comments, rma_id))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'RMA returned to dealer for revision!', 'status': 'pending_dealer'}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 400

    @app.route('/api/authorizer/history', methods=['GET'])
    def get_authorized_rmas():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, u.username as dealer_name, dp.company_name
            FROM rma_requests r
            JOIN users u ON r.dealer_id = u.id
            JOIN dealer_profiles dp ON u.id = dp.user_id
            WHERE r.authorized_by IS NOT NULL
            ORDER BY r.authorized_date DESC, r.updated_at DESC
        ''')
        rmas = []
        for row in cursor.fetchall():
            rma_dict = dict(row)
            if rma_dict.get('authorizer_attachments'):
                try:
                    rma_dict['authorizer_attachments'] = json.loads(rma_dict['authorizer_attachments'])
                except:
                    rma_dict['authorizer_attachments'] = []
            else:
                rma_dict['authorizer_attachments'] = []
            rmas.append(rma_dict)
        cursor.close()
        conn.close()
        return jsonify({'rmas': rmas}), 200

    @app.route('/api/authorizer/update_authorized/<int:rma_id>', methods=['PUT'])
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT status, authorizer_attachments FROM rma_requests WHERE id = %s', (rma_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA not found'}), 404
        
        if row['status'] not in ['authorized', 'approved', 'pending_approver']:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Cannot edit - RMA status is ' + row['status']}), 400
        
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
            attachments_json = json.dumps(attachment_urls) if attachment_urls else None
        else:
            attachments_json = row['authorizer_attachments']
        
        try:
            cursor.execute('''
                UPDATE rma_requests SET
                    authorized_by = %s,
                    return_date = %s,
                    return_received_by = %s,
                    authorizer_comments = %s,
                    authorizer_attachments = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (authorized_by, return_date, return_received_by, authorizer_comments, attachments_json, rma_id))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'Authorization details updated successfully!'}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': str(e)}), 400