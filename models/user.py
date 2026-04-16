import bcrypt
from database.db import get_db_connection, get_placeholder
from config import Config

class User:
    @staticmethod
    def create(username, password, role, email=None, contact_number=None):
        """Create new user"""
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db_connection()
        if not conn:
            return {'success': False, 'error': 'Database connection failed'}
        
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        try:
            cursor.execute(f'''
                INSERT INTO users (username, password, role, email, contact_number) 
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (username, hashed.decode('utf-8'), role, email, contact_number))
            conn.commit()
            
            # Get the last inserted ID
            cursor.execute(f'SELECT id FROM users WHERE username = {placeholder}', (username,))
            user_id = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return {'success': True, 'user_id': user_id}
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        placeholder = get_placeholder()
        cursor.execute(f'SELECT * FROM users WHERE username = {placeholder}', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            if Config.USE_POSTGRES:
                return dict(user)
            else:
                columns = ['id', 'username', 'password', 'role', 'email', 'contact_number', 'created_at']
                return dict(zip(columns, user))
        return None
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        placeholder = get_placeholder()
        cursor.execute(f'SELECT * FROM users WHERE id = {placeholder}', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            if Config.USE_POSTGRES:
                return dict(user)
            else:
                columns = ['id', 'username', 'password', 'role', 'email', 'contact_number', 'created_at']
                return dict(zip(columns, user))
        return None
    
    @staticmethod
    def verify_password(username, password):
        """Verify user password"""
        user = User.find_by_username(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return {'success': True, 'user': user}
        return {'success': False, 'error': 'Invalid username or password'}
    
    @staticmethod
    def create_dealer_profile(user_id, company_name, region, province, city, barangay):
        """Create dealer profile after registration with region and province"""
        conn = get_db_connection()
        if not conn:
            return {'success': False, 'error': 'Database connection failed'}
        
        cursor = conn.cursor()
        placeholder = get_placeholder()
        
        try:
            cursor.execute(f'''
                INSERT INTO dealer_profiles (user_id, company_name, region, province, city, barangay)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (user_id, company_name, region, province, city, barangay))
            conn.commit()
            cursor.close()
            conn.close()
            return {'success': True}
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_dealer_profile(user_id):
        """Get dealer profile by user_id"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        placeholder = get_placeholder()
        cursor.execute(f'''
            SELECT company_name, region, province, city, barangay, is_approved 
            FROM dealer_profiles WHERE user_id = {placeholder}
        ''', (user_id,))
        profile = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if profile:
            if Config.USE_POSTGRES:
                return dict(profile)
            else:
                columns = ['company_name', 'region', 'province', 'city', 'barangay', 'is_approved']
                return dict(zip(columns, profile))
        return None
    
    @staticmethod
    def approve_dealer(user_id):
        """Approve dealer account"""
        conn = get_db_connection()
        if not conn:
            return {'success': False, 'error': 'Database connection failed'}
        
        cursor = conn.cursor()
        placeholder = get_placeholder()
        cursor.execute(f'UPDATE dealer_profiles SET is_approved = 1 WHERE user_id = {placeholder}', (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {'success': True}