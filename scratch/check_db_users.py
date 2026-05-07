import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from database.db import get_db_connection
from bson import ObjectId

def check_users():
    print("Connecting to database...")
    try:
        db = get_db_connection()
        print("Connected!")
        users = list(db.users.find({}))
        print(f"Found {len(users)} users.")
        print("Users in database:")
        for user in users:
            print(f"ID: {user['_id']}, Username: {user['username']}, Role: {user['role']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_users()
