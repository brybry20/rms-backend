from flask import request, jsonify
from models.user import User

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
        
        # Validation
        if not all([username, password, email, company_name, city, barangay]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Create user with role 'dealer'
        result = User.create(username, password, 'dealer', email, contact_number)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400
        
        user_id = result['user_id']
        
        # Create dealer profile (company_name is the distributor name)
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
        
        # Check if dealer is approved
        distributor_name = None
        if user['role'] == 'dealer':
            profile = User.get_dealer_profile(user['id'])
            
            if profile and not profile.get('is_approved', 0):
                return jsonify({'error': 'Your account is pending admin approval'}), 401
            
            # Get company_name as distributor_name
            if profile:
                distributor_name = profile.get('company_name')
        
        return jsonify({
            'message': 'Login successful!',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'distributor_name': distributor_name  # ✅ Ito ang ipapasa sa frontend
            }
        }), 200
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'ok', 'message': 'RMA System API is running'}), 200