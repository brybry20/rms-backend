from flask import request, jsonify
from models.rma import RMA
from database.db import get_db_connection

def register_dealer_routes(app):
    
    @app.route('/api/dealer/rma/create', methods=['POST'])
    def create_rma():
        try:
            # Handle form data with files
            data = request.form.to_dict()
            files = request.files.getlist('attachments')
            
            dealer_id = data.get('dealer_id')
            
            if not dealer_id:
                return jsonify({'error': 'dealer_id required'}), 400
            
            # Convert warranty string to boolean
            if 'warranty' in data:
                data['warranty'] = data['warranty'] == 'true'
            
            # Handle files - read bytes for Cloudinary
            uploaded_files = []
            for file in files:
                if file and file.filename:
                    file_bytes = file.read()
                    uploaded_files.append(file_bytes)
            
            # Debug: Print received data
            print(f"Received data: {data}")
            print(f"Files count: {len(uploaded_files)}")
            
            result = RMA.create(data, uploaded_files)
            
            if result['success']:
                return jsonify({
                    'message': 'RMA request created successfully!',
                    'rma_id': result['rma_id'],
                    'rma_number': result['rma_number'],
                    'attachments': result.get('attachments', [])
                }), 201
            else:
                return jsonify({'error': result['error']}), 400
        except Exception as e:
            import traceback
            return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
    
    @app.route('/api/dealer/rma/my-requests/<int:dealer_id>', methods=['GET'])
    def get_my_rmas(dealer_id):
        rmas = RMA.get_by_dealer(dealer_id)
        return jsonify({'rmas': rmas}), 200
    
    @app.route('/api/dealer/rma/<int:rma_id>/<int:dealer_id>', methods=['GET'])
    def get_rma_by_id(rma_id, dealer_id):
        rma = RMA.get_by_id(rma_id, dealer_id)
        if rma:
            return jsonify({'rma': rma}), 200
        else:
            return jsonify({'error': 'RMA not found'}), 404
    
    @app.route('/api/dealer/rma/update/<int:rma_id>/<int:dealer_id>', methods=['PUT'])
    def update_dealer_rma(rma_id, dealer_id):
        data = request.get_json()
        result = RMA.update(rma_id, dealer_id, data)
        
        if result['success']:
            return jsonify({'message': 'RMA updated successfully!'}), 200
        else:
            return jsonify({'error': result['error']}), 400
    
    @app.route('/api/dealer/rma/delete/<int:rma_id>/<int:dealer_id>', methods=['DELETE'])
    def delete_dealer_rma(rma_id, dealer_id):
        result = RMA.delete(rma_id, dealer_id)
        
        if result['success']:
            return jsonify({'message': 'RMA deleted successfully!'}), 200
        else:
            return jsonify({'error': result['error']}), 400
        
    @app.route('/api/dealer/profile/<int:dealer_id>', methods=['GET'])
    def get_dealer_profile(dealer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dp.company_name, dp.city, dp.barangay
            FROM dealer_profiles dp
            WHERE dp.user_id = %s
        ''', (dealer_id,))
        profile = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if profile:
            return jsonify({'profile': dict(profile)}), 200
        else:
            return jsonify({'profile': None}), 200
    @app.route('/api/debug-rma-create', methods=['POST'])
    def debug_rma_create():
        try:
            from models.rma import RMA
            import traceback
            
            print("=" * 50)
            print("DEBUG: RMA Create called")
            print(f"Form data: {request.form.to_dict()}")
            print(f"Files: {request.files}")
            
            data = request.form.to_dict()
            files = request.files.getlist('attachments')
            
            dealer_id = data.get('dealer_id')
            if not dealer_id:
                return jsonify({'error': 'dealer_id required'}), 400
            
            if 'warranty' in data:
                data['warranty'] = data['warranty'] == 'true'
            
            uploaded_files = []
            for file in files:
                if file and file.filename:
                    file_bytes = file.read()
                    uploaded_files.append(file_bytes)
            
            result = RMA.create(data, uploaded_files)
            
            return jsonify(result), 200 if result['success'] else 400
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500