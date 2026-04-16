from pymongo import MongoClient
from datetime import datetime

# I-PALITAN ANG <db_username> at <db_password> ng actual credentials mo!
# Example: mongodb+srv://bryanbryan:bryan20@cluster0.nzulea8.mongodb.net/?appName=Cluster0

MONGO_URI = "mongodb+srv://bryanbryan:bryan20@cluster0.nzulea8.mongodb.net/?appName=Cluster0"
#           ^^^^^^^^^^^^ ^^^^^^^
#           username     password

def test_connection():
    print("=" * 50)
    print("TESTING MONGODB ATLAS CONNECTION")
    print("=" * 50)
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        
        # Test the connection
        client.admin.command('ping')
        print("✅ SUCCESS: Connected to MongoDB Atlas!")
        
        # Get database info
        print(f"\n📊 Database Info:")
        print(f"   - Connection String: {MONGO_URI[:50]}...")
        
        # List all databases
        print("\n📁 Available Databases:")
        for db_name in client.list_database_names():
            print(f"   - {db_name}")
        
        # Use a specific database
        db = client.get_database("rma_test_db")
        
        # Create a test collection
        print("\n📝 Creating test collection...")
        test_collection = db.test_connection
        
        # Insert a test document
        test_doc = {
            "test_id": 1,
            "message": "Hello from RMA System!",
            "timestamp": datetime.now(),
            "status": "success"
        }
        
        result = test_collection.insert_one(test_doc)
        print(f"✅ Inserted document with ID: {result.inserted_id}")
        
        # Query the test document
        print("\n🔍 Querying test document...")
        found = test_collection.find_one({"test_id": 1})
        if found:
            print(f"✅ Found document:")
            print(f"   - ID: {found['_id']}")
            print(f"   - Message: {found['message']}")
            print(f"   - Timestamp: {found['timestamp']}")
        
        # Clean up
        print("\n🧹 Cleaning up test data...")
        test_collection.drop()
        print("✅ Test collection removed")
        
        # Close connection
        client.close()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED! MongoDB is ready to use!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {e}")
        print("\nPossible issues:")
        print("1. Check your username and password")
        print("2. Check if the cluster name is correct")
        print("3. Check if your IP address is whitelisted in MongoDB Atlas")
        print("4. Check if the database user has proper permissions")
        return False

def test_rma_collections():
    """Test creating RMA collections"""
    print("\n" + "=" * 50)
    print("TESTING RMA COLLECTIONS CREATION")
    print("=" * 50)
    
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database("rma_system")
        
        # Create collections
        collections = ["users", "dealer_profiles", "rma_requests", "notifications"]
        
        for col_name in collections:
            if col_name not in db.list_collection_names():
                db.create_collection(col_name)
                print(f"✅ Created collection: {col_name}")
            else:
                print(f"⚠️ Collection already exists: {col_name}")
        
        # Create indexes
        db.users.create_index("username", unique=True)
        db.rma_requests.create_index("rma_number", unique=True)
        db.rma_requests.create_index("status")
        db.rma_requests.create_index("dealer_id")
        
        print("\n✅ Indexes created successfully!")
        
        # Show all collections
        print("\n📁 Collections in 'rma_system' database:")
        for col in db.list_collection_names():
            print(f"   - {col}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_crud_operations():
    """Test basic CRUD operations"""
    print("\n" + "=" * 50)
    print("TESTING CRUD OPERATIONS")
    print("=" * 50)
    
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database("rma_system")
        
        # CREATE
        print("\n1. CREATE - Inserting test user...")
        test_user = {
            "username": "testuser",
            "email": "test@example.com",
            "role": "dealer",
            "created_at": datetime.now()
        }
        result = db.users.insert_one(test_user)
        user_id = result.inserted_id
        print(f"   ✅ Inserted with ID: {user_id}")
        
        # READ
        print("\n2. READ - Finding test user...")
        found = db.users.find_one({"username": "testuser"})
        if found:
            print(f"   ✅ Found: {found['username']} - {found['email']}")
        else:
            print("   ❌ Not found")
        
        # UPDATE
        print("\n3. UPDATE - Updating test user...")
        update_result = db.users.update_one(
            {"username": "testuser"},
            {"$set": {"email": "updated@example.com"}}
        )
        print(f"   ✅ Modified: {update_result.modified_count} document(s)")
        
        # DELETE
        print("\n4. DELETE - Removing test user...")
        delete_result = db.users.delete_one({"username": "testuser"})
        print(f"   ✅ Deleted: {delete_result.deleted_count} document(s)")
        
        client.close()
        
        print("\n✅ All CRUD operations successful!")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def main():
    print("\n" + "🔵" * 30)
    print("   MONGODB ATLAS CONNECTION TEST")
    print("🔵" * 30 + "\n")
    
    # Test 1: Basic connection
    if not test_connection():
        print("\n❌ Cannot proceed - connection failed!")
        return
    
    # Test 2: Create RMA collections
    test_rma_collections()
    
    # Test 3: Test CRUD operations
    test_crud_operations()
    
    print("\n" + "🎉" * 30)
    print("   MONGODB IS READY FOR RMA SYSTEM!")
    print("🎉" * 30)

if __name__ == "__main__":
    main()