import bcrypt
from database.db import get_db_connection
from datetime import datetime
from bson import ObjectId

class User:
    
    @staticmethod
    def _serialize(doc):
        """Convert MongoDB document to dictionary with string id"""
        if doc:
            doc['id'] = str(doc.pop('_id'))
        return doc
    
    @staticmethod
    def create(username, password, role, email=None, contact_number=None):
        """Create new user"""
        db = get_db_connection()
        
        # Check if username already exists
        if db.users.find_one({"username": username}):
            return {'success': False, 'error': 'Username already exists'}
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user = {
            "username": username,
            "password": hashed.decode('utf-8'),
            "role": role,
            "email": email,
            "contact_number": contact_number,
            "created_at": datetime.now()
        }
        
        try:
            result = db.users.insert_one(user)
            return {'success': True, 'user_id': str(result.inserted_id)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        db = get_db_connection()
        user = db.users.find_one({"username": username})
        return User._serialize(user)
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        db = get_db_connection()
        try:
            user = db.users.find_one({"_id": ObjectId(user_id)})
            return User._serialize(user)
        except:
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
        db = get_db_connection()
        
        # Check if profile already exists
        if db.dealer_profiles.find_one({"user_id": user_id}):
            return {'success': False, 'error': 'Dealer profile already exists'}
        
        profile = {
            "user_id": user_id,
            "company_name": company_name,
            "region": region,
            "province": province,
            "city": city,
            "barangay": barangay,
            "is_approved": 0,
            "registered_at": datetime.now()
        }
        
        try:
            db.dealer_profiles.insert_one(profile)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_dealer_profile(user_id):
        """Get dealer profile by user_id"""
        db = get_db_connection()
        profile = db.dealer_profiles.find_one({"user_id": user_id})
        if profile:
            profile['id'] = str(profile.pop('_id'))
        return profile
    
    @staticmethod
    def approve_dealer(user_id):
        """Approve dealer account"""
        db = get_db_connection()
        result = db.dealer_profiles.update_one(
            {"user_id": user_id},
            {"$set": {"is_approved": 1}}
        )
        if result.modified_count > 0:
            return {'success': True}
        return {'success': False, 'error': 'Dealer not found'}
    
    @staticmethod
    def get_all_dealers():
        """Get all dealers with their profiles"""
        db = get_db_connection()
        
        # Get all dealer users
        dealers = list(db.users.find({"role": "dealer"}))
        
        result = []
        for dealer in dealers:
            dealer_dict = User._serialize(dealer)
            # Get dealer profile
            profile = db.dealer_profiles.find_one({"user_id": dealer_dict['id']})
            if profile:
                profile['id'] = str(profile.pop('_id'))
                dealer_dict['profile'] = profile
            result.append(dealer_dict)
        
        return result
    
    @staticmethod
    def get_pending_dealers():
        """Get all pending dealers (not approved)"""
        db = get_db_connection()
        
        # Get all dealer profiles that are not approved
        pending_profiles = list(db.dealer_profiles.find({"is_approved": 0}))
        
        result = []
        for profile in pending_profiles:
            # Find the user by user_id (convert string to ObjectId)
            try:
                user = db.users.find_one({"_id": ObjectId(profile["user_id"])})
                if user:
                    dealer_dict = {
                        "id": str(user["_id"]),
                        "username": user.get("username"),
                        "email": user.get("email"),
                        "contact_number": user.get("contact_number"),
                        "role": user.get("role"),
                        "created_at": user.get("created_at"),
                        "company_name": profile.get("company_name"),
                        "region": profile.get("region"),
                        "province": profile.get("province"),
                        "city": profile.get("city"),
                        "barangay": profile.get("barangay"),
                        "registered_at": profile.get("registered_at"),
                        "is_approved": profile.get("is_approved")
                    }
                    result.append(dealer_dict)
            except:
                # If user_id is not a valid ObjectId, skip
                continue
        
        return result
    
    @staticmethod
    def update_dealer_profile(user_id, data):
        """Update dealer profile"""
        db = get_db_connection()
        
        # Update user info
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "username": data.get('username'),
                "email": data.get('email'),
                "contact_number": data.get('contact_number')
            }}
        )
        
        # Update dealer profile
        result = db.dealer_profiles.update_one(
            {"user_id": user_id},
            {"$set": {
                "company_name": data.get('company_name'),
                "region": data.get('region'),
                "province": data.get('province'),
                "city": data.get('city'),
                "barangay": data.get('barangay')
            }}
        )
        
        return {'success': True, 'modified': result.modified_count}
    
    @staticmethod
    def change_password(user_id, new_password):
        """Change user password"""
        db = get_db_connection()
        
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": hashed.decode('utf-8')}}
        )
        
        if result.modified_count > 0:
            return {'success': True}
        return {'success': False, 'error': 'User not found'}