from flask import request, jsonify
from models.user import User
from database.db import get_db_connection, get_placeholder
from config import Config
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
        region = data.get('region')
        province = data.get('province')
        city = data.get('city')
        barangay = data.get('barangay')
        
        # Check for missing fields
        missing_fields = []
        if not username: missing_fields.append('username')
        if not password: missing_fields.append('password')
        if not email: missing_fields.append('email')
        if not company_name: missing_fields.append('company_name')
        if not region: missing_fields.append('region')
        if not province: missing_fields.append('province')
        if not city: missing_fields.append('city')
        if not barangay: missing_fields.append('barangay')
        
        if missing_fields:
            return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
        
        result = User.create(username, password, 'dealer', email, contact_number)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400
        
        user_id = result['user_id']
        
        profile_result = User.create_dealer_profile(user_id, company_name, region, province, city, barangay)
        
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
            
            if not profile:
                return jsonify({'error': 'Dealer profile not found'}), 401
            
            if not profile.get('is_approved', 0):
                return jsonify({'error': 'Your account is pending admin approval. Please wait for confirmation.'}), 401
            
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
    
    @app.route('/api/reset-database', methods=['POST'])
    def reset_database():
        from database.db import reset_database as reset_db
        reset_db()
        return jsonify({'message': 'Database reset successfully!'}), 200

    @app.route('/api/debug-register-full', methods=['POST'])
    def debug_register_full():
        try:
            from models.user import User
            data = request.get_json()
            
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            contact_number = data.get('contact_number')
            company_name = data.get('company_name')
            region = data.get('region')
            province = data.get('province')
            city = data.get('city')
            barangay = data.get('barangay')
            
            # Test User.create
            print("Creating user...")
            result = User.create(username, password, 'dealer', email, contact_number)
            print(f"User.create result: {result}")
            
            if not result['success']:
                return jsonify({'error': f'User.create failed: {result["error"]}'}), 400
            
            user_id = result['user_id']
            
            # Test create_dealer_profile
            print("Creating dealer profile...")
            profile_result = User.create_dealer_profile(user_id, company_name, region, province, city, barangay)
            print(f"Profile result: {profile_result}")
            
            if not profile_result['success']:
                return jsonify({'error': f'create_dealer_profile failed: {profile_result["error"]}'}), 400
            
            return jsonify({
                'message': 'Registration successful!',
                'user_id': user_id
            }), 201
            
        except Exception as e:
            import traceback
            return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
    
    @app.route('/api/create-default-users', methods=['POST'])
    def create_default_users():
        """Temporary endpoint to create all default users"""
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        default_users = [
            {'username': 'admin', 'password': 'admin123', 'role': 'super_admin', 'email': 'admin@rma.com', 'contact': '09123456789'},
            {'username': 'auth', 'password': 'auth123', 'role': 'authorizer', 'email': 'authorizer@rma.com', 'contact': '09123456788'},
            {'username': 'app', 'password': 'app123', 'role': 'approver', 'email': 'approver@rma.com', 'contact': '09123456787'},
        ]
        
        created_users = []
        existing_users = []
        
        for user_data in default_users:
            cursor.execute(f'SELECT id FROM users WHERE username = {placeholder}', (user_data['username'],))
            if cursor.fetchone():
                existing_users.append(user_data['username'])
                continue
            
            hashed = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute(f'''
                INSERT INTO users (username, password, role, email, contact_number)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (user_data['username'], hashed.decode('utf-8'), user_data['role'], user_data['email'], user_data['contact']))
            
            created_users.append(user_data['username'])
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Default users created successfully!',
            'created': created_users,
            'already_exist': existing_users,
            'users': [
                {'username': 'admin', 'password': 'admin123', 'role': 'super_admin'},
                {'username': 'auth', 'password': 'auth123', 'role': 'authorizer'},
                {'username': 'app', 'password': 'app123', 'role': 'approver'},
            ]
        }), 201