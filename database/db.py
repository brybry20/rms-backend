import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, 'rma.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
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
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # RMA Requests
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rma_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rma_number TEXT UNIQUE NOT NULL,
            dealer_id INTEGER,
            return_type TEXT,
            reason_for_return TEXT,
            warranty INTEGER DEFAULT 0,
            filer_name TEXT,
            distributor_name TEXT,
            date_filled TEXT,
            product TEXT,
            product_description TEXT,
            work_environment TEXT,
            po_number TEXT,
            sales_invoice_number TEXT,
            shipping_date TEXT,
            return_date TEXT,
            end_user_company TEXT,
            end_user_location TEXT,
            end_user_industry TEXT,
            end_user_contact_person TEXT,
            problem_description TEXT,
            dealer_comments TEXT,
            authorized_by TEXT,
            authorized_date TEXT,
            return_received_by TEXT,
            authorizer_comments TEXT,
            approved_by TEXT,
            approved_date TEXT,
            approved_with TEXT,
            replacement_order_no TEXT,
            closed_date TEXT,
            approver_comments TEXT,
            attachments TEXT,
            authorizer_attachments TEXT,
            approver_attachments TEXT,
            status TEXT DEFAULT 'pending_dealer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized!")