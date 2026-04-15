from flask import request, jsonify
from models.user import User
from database.db import get_db_connection
import bcrypt

def register_routes(app):
    
    @app.route('/api/register', methods=['POST'])
    def register():
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        contact_number = data.get('contact_number')
        company_name = data.get('company_name')
        city = data.get('city')
        barangay = data.get('barangay')
        
        if not all([username, password, email, company_name, city, barangay]):
            return jsonify({'error': 'All fields are required'}), 400
        
        result = User.create(username, password, 'dealer', email, contact_number)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400
        
        user_id = result['user_id']
        
        profile_result = User.create_dealer_profile(user_id, company_name, city, barangay)
        
        if not profile_result['success']:
            return jsonify({'error': profile_result['error']}), 400
        
        return jsonify({
            'message': 'Registration successful! Please wait for admin approval.',
            'user_id': user_id
        }), 201
    
    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        result = User.verify_password(username, password)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 401
        
        user = result['user']
        
        distributor_name = None
        if user['role'] == 'dealer':
            profile = User.get_dealer_profile(user['id'])
            if profile and not profile.get('is_approved', 0):
                return jsonify({'error': 'Your account is pending admin approval'}), 401
            if profile:
                distributor_name = profile.get('company_name')
        
        return jsonify({
            'message': 'Login successful!',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'distributor_name': distributor_name
            }
        }), 200
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'ok', 'message': 'RMA System API is running'}), 200
    
    # ✅ TEMPORARY ENDPOINT - Create default users (remove after use)
    @app.route('/api/create-default-users', methods=['POST'])
    def create_default_users():
        """Temporary endpoint to create all default users"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        default_users = [
            {'username': 'admin', 'password': 'admin123', 'role': 'super_admin', 'email': 'admin@rma.com', 'contact': '09123456789'},
            {'username': 'authorizer1', 'password': 'auth123', 'role': 'authorizer', 'email': 'authorizer@rma.com', 'contact': '09123456788'},
            {'username': 'approver1', 'password': 'approve123', 'role': 'approver', 'email': 'approver@rma.com', 'contact': '09123456787'},
            {'username': 'dealer1', 'password': 'dealer123', 'role': 'dealer', 'email': 'dealer@rma.com', 'contact': '09123456786'},
        ]
        
        created_users = []
        existing_users = []
        
        for user_data in default_users:
            cursor.execute('SELECT id FROM users WHERE username = %s', (user_data['username'],))
            if cursor.fetchone():
                existing_users.append(user_data['username'])
                continue
            
            hashed = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute('''
                INSERT INTO users (username, password, role, email, contact_number)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_data['username'], hashed.decode('utf-8'), user_data['role'], user_data['email'], user_data['contact']))
            
            user_id = cursor.lastrowid
            created_users.append(user_data['username'])
            
            if user_data['role'] == 'dealer':
                cursor.execute('''
                    INSERT INTO dealer_profiles (user_id, company_name, city, barangay, is_approved)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (user_id, 'Deltaplus Distributor', 'Quezon City', 'Barangay Central', 1))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Default users created!',
            'created': created_users,
            'already_exist': existing_users,
            'users': [
                {'username': 'admin', 'password': 'admin123', 'role': 'super_admin'},
                {'username': 'authorizer1', 'password': 'auth123', 'role': 'authorizer'},
                {'username': 'approver1', 'password': 'approve123', 'role': 'approver'},
                {'username': 'dealer1', 'password': 'dealer123', 'role': 'dealer'},
            ]
        }), 201