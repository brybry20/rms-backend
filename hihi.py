import bcrypt
import sqlite3
import os
from database.db import get_db_connection
from config import Config

def recreate_and_seed():
    # First, recreate all tables using db.py
    from database.db import init_db
    init_db()
    
    print("\n" + "=" * 50)
    print("📝 ADDING DEFAULT USERS")
    print("=" * 50)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    default_users = [
        ('admin', 'admin123', 'super_admin', 'admin@rma.com', '09123456789'),
        ('auth', 'auth123', 'authorizer', 'authorizer@rma.com', '09123456788'),
        ('app', 'app123', 'approver', 'approver@rma.com', '09123456787')
    ]
    
    for username, plain_password, role, email, contact in default_users:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            hashed = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO users (username, password, role, email, contact_number)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, hashed.decode('utf-8'), role, email, contact))
            print(f"✅ Created {role}: {username} / {plain_password}")
        else:
            print(f"⚠️ {username} already exists")
    
    conn.commit()
    conn.close()
    
    print("\n✅ DONE!")
    print("\n📝 Default Users:")
    print("  - super_admin: admin / admin123")
    print("  - authorizer: auth / auth123")
    print("  - approver: app / app123")

if __name__ == '__main__':
    recreate_and_seed()