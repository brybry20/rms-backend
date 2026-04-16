import bcrypt
import sqlite3
from database.db import get_db_connection

class User:
    @staticmethod
    def create(username, password, role, email=None, contact_number=None):
        """Create new user"""
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db_connection()
        if not conn:
            return {'success': False, 'error': 'Database connection failed'}
        
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password, role, email, contact_number) 
                VALUES (?, ?, ?, ?, ?)
            ''', (username, hashed.decode('utf-8'), role, email, contact_number))
            user_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            return {'success': True, 'user_id': user_id}
        except sqlite3.IntegrityError:
            conn.rollback()
            cursor.close()
            conn.close()
            return {'success': False, 'error': 'Username already exists'}
    
    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return dict(user)
        return None
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return dict(user)
        return None
    
    @staticmethod
    def verify_password(username, password):
        """Verify user password"""
        user = User.find_by_username(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return {'success': True, 'user': user}
        return {'success': False, 'error': 'Invalid username or password'}
    
    @staticmethod
    def create_dealer_profile(user_id, company_name, city, barangay):
        """Create dealer profile after registration"""
        conn = get_db_connection()
        if not conn:
            return {'success': False, 'error': 'Database connection failed'}
        
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO dealer_profiles (user_id, company_name, city, barangay)
                VALUES (?, ?, ?, ?)
            ''', (user_id, company_name, city, barangay))
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
        cursor.execute('SELECT company_name, city, barangay, is_approved FROM dealer_profiles WHERE user_id = ?', (user_id,))
        profile = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if profile:
            return dict(profile)
        return None
    
    @staticmethod
    def approve_dealer(user_id):
        """Approve dealer account"""
        conn = get_db_connection()
        if not conn:
            return {'success': False, 'error': 'Database connection failed'}
        
        cursor = conn.cursor()
        cursor.execute('UPDATE dealer_profiles SET is_approved = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {'success': True}