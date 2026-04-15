import sqlite3
import os
from config import Config

def get_db_connection():
    """Create database connection to SQLite"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Para makuha ang columns as dictionary
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def init_db():
    """Initialize all tables"""
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    # Users table (lahat ng users)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT,
            contact_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Dealer profiles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dealer_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            company_name TEXT,
            city TEXT,
            barangay TEXT,
            is_approved INTEGER DEFAULT 0,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # RMA Requests
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rma_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rma_number TEXT UNIQUE NOT NULL,
            dealer_id INTEGER,
            
            -- Return Merchandise Authorization
            return_type TEXT,
            reason_for_return TEXT,
            warranty INTEGER DEFAULT 0,
            product_description TEXT,
            work_environment TEXT,
            distributor_name TEXT,
            po_number TEXT,
            sales_invoice_number TEXT,
            shipping_date TEXT,
            return_date TEXT,
            
            -- End User Details
            end_user_company TEXT,
            end_user_location TEXT,
            end_user_industry TEXT,
            end_user_contact_person TEXT,
            
            -- Problem & Comments
            problem_description TEXT,
            dealer_comments TEXT,
            
            -- Authorization Details
            authorized_by INTEGER,
            authorized_date TEXT,
            return_received_by TEXT,
            authorizer_comments TEXT,
            
            -- Approval Details
            approved_by INTEGER,
            approved_date TEXT,
            approved_with TEXT,
            replacement_order_no TEXT,
            closed_date TEXT,
            approver_comments TEXT,
            
            -- Status
            status TEXT DEFAULT 'pending_dealer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dealer_id) REFERENCES users (id),
            FOREIGN KEY (authorized_by) REFERENCES users (id),
            FOREIGN KEY (approved_by) REFERENCES users (id)
        )
    ''')
    
    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            message TEXT,
            type TEXT,
            is_read INTEGER DEFAULT 0,
            related_rma_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (related_rma_id) REFERENCES rma_requests (id)
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ SQLite database and tables created successfully!")