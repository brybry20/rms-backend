import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load .env from backend folder
load_dotenv('backend/.env')

MONGO_URI = os.getenv('MONGO_URI')
MONGO_DATABASE = os.getenv('MONGO_DATABASE')

def check_counts():
    print(f"Connecting to: {MONGO_DATABASE}...")
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DATABASE]
    
    rma_count = db.rma_requests.count_documents({})
    user_count = db.users.count_documents({})
    dealer_count = db.dealer_profiles.count_documents({})
    
    print(f"RMA Requests: {rma_count}")
    print(f"Users: {user_count}")
    print(f"Dealer Profiles: {dealer_count}")
    
    # Status breakdown
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    statuses = list(db.rma_requests.aggregate(pipeline))
    print("\nStatus Breakdown:")
    for s in statuses:
        print(f" - {s['_id']}: {s['count']}")
    
    if rma_count > 0:
        print("\nLatest RMA details:")
        latest = db.rma_requests.find_one(sort=[("created_at", -1)])
        print(f"RMA Number: {latest.get('rma_number')}")
        print(f"Status: {latest.get('status')}")
        dealer_id = latest.get('dealer_id')
        print(f"Dealer ID: {dealer_id} (Type: {type(dealer_id)})")
        
        # Check if it matches any user
        user = db.users.find_one({"_id": dealer_id})
        print(f"Match with User (direct): {user is not None}")
        
        if isinstance(dealer_id, str):
            from bson import ObjectId
            try:
                user_oid = db.users.find_one({"_id": ObjectId(dealer_id)})
                print(f"Match with User (ObjectId): {user_oid is not None}")
            except:
                print("Dealer ID is not a valid ObjectId string")

if __name__ == "__main__":
    check_counts()
