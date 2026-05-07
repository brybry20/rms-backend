import os
import sys
from bson import ObjectId

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database.db import init_db
from models.rma import RMA
from dotenv import load_dotenv

# Load .env from backend folder
load_dotenv('backend/.env')

def verify_fix():
    print("Verifying backend data fetching fix...")
    init_db()
    
    print("\n--- Testing get_pending_for_authorizer ---")
    authorizer_rmas = RMA.get_pending_for_authorizer()
    print(f"Found {len(authorizer_rmas)} pending RMAs for authorizer")
    for rma in authorizer_rmas:
        print(f"RMA: {rma['rma_number']}, Status: {rma['status']}")
        print(f"Company: {rma.get('company_name', 'MISSING')}")
        print(f"Distributor: {rma.get('distributor_name', 'N/A')}")
        if 'dealer' in rma:
            print(f"  Dealer email: {rma['dealer'].get('email')}")
        else:
            print("  Dealer info MISSING")
        
        if 'profile' in rma:
            print(f"  Profile found: {rma['profile'].keys()}")
            print(f"  Profile company_name: {rma['profile'].get('company_name')}")
        else:
            print("  Profile MISSING")

    print("\n--- Testing get_all ---")
    all_rmas = RMA.get_all()
    print(f"Found {len(all_rmas)} total RMAs")
    for rma in all_rmas:
        print(f"RMA: {rma['rma_number']}, Status: {rma['status']}, Company: {rma.get('company_name', 'MISSING')}")

if __name__ == "__main__":
    verify_fix()
