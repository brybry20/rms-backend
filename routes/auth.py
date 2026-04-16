from flask import request, jsonify
from models.user import User
from database.db import get_db_connection
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
    
    # Helper function to get the correct placeholder
    def get_placeholder():
        return '%s' if Config.USE_POSTGRES else '?'
    
    # ✅ TEMPORARY ENDPOINT - Create default users (works with both SQLite and PostgreSQL)
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
            # Use the correct placeholder for the database
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