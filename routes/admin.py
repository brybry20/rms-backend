from flask import request, jsonify
from models.user import User

def register_admin_routes(app):
    
    @app.route('/api/admin/pending-dealers', methods=['GET'])
    def get_pending_dealers():
        from database.db import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.contact_number, 
                   dp.company_name, dp.region, dp.province, dp.city, dp.barangay, dp.registered_at
            FROM users u
            JOIN dealer_profiles dp ON u.id = dp.user_id
            WHERE u.role = 'dealer' AND dp.is_approved = 0
        ''')
        
        dealers = []
        for row in cursor.fetchall():
            dealers.append(dict(row))
        
        cursor.close()
        conn.close()
        
        return jsonify({'dealers': dealers}), 200
    
    @app.route('/api/admin/approve-dealer/<int:user_id>', methods=['PUT'])
    def approve_dealer(user_id):
        result = User.approve_dealer(user_id)
        
        if result['success']:
            return jsonify({'message': 'Dealer approved successfully!'}), 200
        else:
            return jsonify({'error': result['error']}), 400
    
    @app.route('/api/admin/reject-dealer/<int:user_id>', methods=['DELETE'])
    def reject_dealer(user_id):
        from database.db import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id FROM users u
            JOIN dealer_profiles dp ON u.id = dp.user_id
            WHERE u.id = %s AND u.role = 'dealer' AND dp.is_approved = 0
        ''', (user_id,))
        
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Dealer not found or already approved'}), 404
        
        cursor.execute('DELETE FROM dealer_profiles WHERE user_id = %s', (user_id,))
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Dealer rejected and deleted successfully!'}), 200
    
    @app.route('/api/admin/all-dealers', methods=['GET'])
    def get_all_dealers():
        from database.db import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.contact_number, u.created_at as registered_at,
                   dp.company_name, dp.region, dp.province, dp.city, dp.barangay, dp.is_approved, dp.registered_at
            FROM users u
            JOIN dealer_profiles dp ON u.id = dp.user_id
            WHERE u.role = 'dealer'
            ORDER BY dp.registered_at DESC
        ''')
        
        dealers = []
        for row in cursor.fetchall():
            dealers.append(dict(row))
        
        cursor.close()
        conn.close()
        
        return jsonify({'dealers': dealers}), 200
    
    @app.route('/api/admin/all-rma', methods=['GET'])
    def get_all_rma():
        from database.db import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, 
                   u.username as dealer_name, 
                   dp.company_name,
                   au.username as authorizer_name,
                   ap.username as approver_name
            FROM rma_requests r
            JOIN users u ON r.dealer_id = u.id
            JOIN dealer_profiles dp ON u.id = dp.user_id
            LEFT JOIN users au ON r.authorized_by = au.id
            LEFT JOIN users ap ON r.approved_by = ap.id
            ORDER BY r.created_at DESC
        ''')
        
        rmas = []
        for row in cursor.fetchall():
            rmas.append(dict(row))
        
        cursor.close()
        conn.close()
        
        return jsonify({'rmas': rmas}), 200
    
    @app.route('/api/admin/rma/<int:rma_id>', methods=['GET'])
    def get_rma_details(rma_id):
        from database.db import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, 
                   u.username as dealer_name, 
                   dp.company_name, dp.region, dp.province, dp.city, dp.barangay,
                   au.username as authorizer_name,
                   ap.username as approver_name
            FROM rma_requests r
            JOIN users u ON r.dealer_id = u.id
            JOIN dealer_profiles dp ON u.id = dp.user_id
            LEFT JOIN users au ON r.authorized_by = au.id
            LEFT JOIN users ap ON r.approved_by = ap.id
            WHERE r.id = %s
        ''', (rma_id,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return jsonify({'rma': dict(row)}), 200
        else:
            return jsonify({'error': 'RMA not found'}), 404
    
    @app.route('/api/admin/rma/<int:rma_id>', methods=['PUT'])
    def update_admin_rma(rma_id):
        from database.db import get_db_connection
        import json
        
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM rma_requests WHERE id = %s', (rma_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA not found'}), 404
        
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
        
        set_clause = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                set_clause.append(f"{field} = %s")
                if field == 'warranty':
                    values.append(1 if data[field] else 0)
                else:
                    values.append(data[field])
        
        if not set_clause:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No fields to update'}), 400
        
        values.append(rma_id)
        
        query = f'''
            UPDATE rma_requests 
            SET {', '.join(set_clause)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        '''
        cursor.execute(query, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'RMA updated successfully!'}), 200
    
    @app.route('/api/admin/rma/<int:rma_id>', methods=['DELETE'])
    def delete_admin_rma(rma_id):
        from database.db import get_db_connection
        import json
        import cloudinary
        import cloudinary.uploader
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT attachments, authorizer_attachments, approver_attachments 
            FROM rma_requests WHERE id = %s
        ''', (rma_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'RMA not found'}), 404
        
        try:
            if row['attachments']:
                atts = json.loads(row['attachments'])
                for att in atts:
                    if att.get('public_id'):
                        cloudinary.uploader.destroy(att['public_id'])
            
            if row['authorizer_attachments']:
                atts = json.loads(row['authorizer_attachments'])
                for att in atts:
                    if att.get('public_id'):
                        cloudinary.uploader.destroy(att['public_id'])
            
            if row['approver_attachments']:
                atts = json.loads(row['approver_attachments'])
                for att in atts:
                    if att.get('public_id'):
                        cloudinary.uploader.destroy(att['public_id'])
        except Exception as e:
            print(f"Error deleting from Cloudinary: {e}")
        
        cursor.execute('DELETE FROM rma_requests WHERE id = %s', (rma_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'RMA deleted successfully!'}), 200
    
    @app.route('/api/admin/stats', methods=['GET'])
    def get_stats():
        from database.db import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM rma_requests 
            GROUP BY status
        ''')
        
        status_counts = {}
        for row in cursor.fetchall():
            status_counts[row['status']] = row['count']
        
        cursor.execute('''
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN dp.is_approved = 1 THEN 1 ELSE 0 END) as approved
            FROM users u
            JOIN dealer_profiles dp ON u.id = dp.user_id
            WHERE u.role = 'dealer'
        ''')
        
        dealer_row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        total = dealer_row['total'] if dealer_row and dealer_row['total'] else 0
        approved = dealer_row['approved'] if dealer_row and dealer_row['approved'] else 0
        pending = total - approved
        
        return jsonify({
            'status_counts': status_counts,
            'dealers': {
                'total': total,
                'approved': approved,
                'pending': pending
            }
        }), 200
    
    @app.route('/api/admin/users', methods=['GET'])
    def get_all_users():
        from database.db import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.role, u.email, u.contact_number, u.created_at,
                   dp.company_name, dp.region, dp.province, dp.city, dp.barangay, dp.is_approved
            FROM users u
            LEFT JOIN dealer_profiles dp ON u.id = dp.user_id
            ORDER BY u.created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append(dict(row))
        
        cursor.close()
        conn.close()
        
        return jsonify({'users': users}), 200

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

    @app.route('/api/admin/dealer/<int:dealer_id>', methods=['PUT'])
    def update_dealer(dealer_id):
        from database.db import get_db_connection
        
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET username = %s, email = %s, contact_number = %s
            WHERE id = %s AND role = 'dealer'
        ''', (data.get('username'), data.get('email'), data.get('contact_number'), dealer_id))
        
        cursor.execute('''
            UPDATE dealer_profiles 
            SET company_name = %s, region = %s, province = %s, city = %s, barangay = %s
            WHERE user_id = %s
        ''', (data.get('company_name'), data.get('region'), data.get('province'), 
              data.get('city'), data.get('barangay'), dealer_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Dealer updated successfully!'}), 200

    @app.route('/api/admin/dealer/<int:dealer_id>/change-password', methods=['PUT'])
    def change_dealer_password(dealer_id):
        from database.db import get_db_connection
        import bcrypt
        
        data = request.get_json()
        new_password = data.get('new_password')
        
        if not new_password or len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET password = %s
            WHERE id = %s AND role = 'dealer'
        ''', (hashed.decode('utf-8'), dealer_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Password changed successfully!'}), 200