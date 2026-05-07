from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import Config
from datetime import datetime

class MongoDB:
    _client = None
    _db = None
    
    @classmethod
    def get_db(cls):
        """Get database connection (singleton pattern)"""
        if cls._db is None:
            try:
                cls._client = MongoClient(Config.MONGO_URI)
                # Test connection
                cls._client.admin.command('ping')
                cls._db = cls._client[Config.MONGO_DATABASE]
                print(f"Connected to MongoDB Atlas! Database: {Config.MONGO_DATABASE}")
                
                # Ensure indexes
                cls._ensure_indexes()
                
            except ConnectionFailure as e:
                print(f"MongoDB connection failed: {e}")
                raise
        return cls._db
    
    @classmethod
    def _ensure_indexes(cls):
        """Create indexes for better performance"""
        db = cls._db
        
        # Users collection indexes
        try:
            db.users.create_index("username", unique=True)
            db.users.create_index("email")
            db.users.create_index("role")
            
            # Dealer profiles indexes
            db.dealer_profiles.create_index("user_id", unique=True)
            db.dealer_profiles.create_index("is_approved")
            
            # RMA requests indexes
            db.rma_requests.create_index("rma_number", unique=True)
            db.rma_requests.create_index("dealer_id")
            db.rma_requests.create_index("status")
            db.rma_requests.create_index("created_at")
            
            # Notifications indexes
            db.notifications.create_index("user_id")
            db.notifications.create_index("is_read")
            
            print("MongoDB indexes created!")
        except Exception as e:
            print(f"Index creation warning: {e}")
    
    @classmethod
    def close(cls):
        """Close the database connection"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            print("MongoDB connection closed")

# Helper functions for backward compatibility
def get_db_connection():
    """Return the database object"""
    return MongoDB.get_db()

def init_db():
    """Initialize database (create collections if not exist)"""
    db = MongoDB.get_db()
    
    # Create collections if not exist (MongoDB creates them automatically on insert)
    collections = ["users", "dealer_profiles", "rma_requests", "notifications"]
    
    for col in collections:
        if col not in db.list_collection_names():
            db.create_collection(col)
            print(f"Created collection: {col}")
    
    print("Database initialization complete!")
    return True

def reset_database():
    """Drop all collections (WARNING: deletes all data!)"""
    db = MongoDB.get_db()
    
    collections = ["users", "dealer_profiles", "rma_requests", "notifications"]
    for col in collections:
        if col in db.list_collection_names():
            db[col].drop()
            print(f"Dropped collection: {col}")
    
    print("Database reset complete!")

def get_placeholder():
    """Placeholder function for compatibility (not needed for MongoDB)"""
    return "%s"