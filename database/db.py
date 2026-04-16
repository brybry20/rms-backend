import sqlite3
import os
import sys

# Add parent directory to path para mahanap ang config.py
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config

def get_db_connection():
    """Create database connection to SQLite"""
    try:
        # Ensure the database directory exists
        db_dir = os.path.dirname(Config.DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def init_db():
    """Initialize all tables with complete schema"""
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
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
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # RMA Requests (COMPLETE schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rma_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rma_number TEXT UNIQUE NOT NULL,
            dealer_id INTEGER,
            
            -- Return Merchandise Authorization
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
            
            -- End User Details
            end_user_company TEXT,
            end_user_location TEXT,
            end_user_industry TEXT,
            end_user_contact_person TEXT,
            
            -- Problem & Comments
            problem_description TEXT,
            dealer_comments TEXT,
            
            -- Attachments
            attachments TEXT,
            
            -- Authorization Details
            authorized_by INTEGER,
            authorized_date TEXT,
            return_received_by TEXT,
            authorizer_comments TEXT,
            authorizer_attachments TEXT,
            
            -- Approval Details
            approved_by INTEGER,
            approved_date TEXT,
            approved_with TEXT,
            replacement_order_no TEXT,
            closed_date TEXT,
            approver_comments TEXT,
            approver_attachments TEXT,
            
            -- Status
            status TEXT DEFAULT 'pending_dealer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (dealer_id) REFERENCES users (id) ON DELETE SET NULL,
            FOREIGN KEY (authorized_by) REFERENCES users (id) ON DELETE SET NULL,
            FOREIGN KEY (approved_by) REFERENCES users (id) ON DELETE SET NULL
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
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (related_rma_id) REFERENCES rma_requests (id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_dealer_profiles_user_id ON dealer_profiles(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_dealer_profiles_is_approved ON dealer_profiles(is_approved)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rma_dealer_id ON rma_requests(dealer_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rma_status ON rma_requests(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rma_rma_number ON rma_requests(rma_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rma_created_at ON rma_requests(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rma_dealer_status ON rma_requests(dealer_id, status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)')
    
    conn.commit()
    
    # Create trigger for updated_at
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_rma_requests_timestamp 
        AFTER UPDATE ON rma_requests
        BEGIN
            UPDATE rma_requests SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ SQLite database and tables created successfully!")
    print("✅ Added columns: authorizer_attachments, approver_attachments")
    print("✅ Indexes and triggers added for performance!")

def migrate_existing_database():
    """Mag-add ng missing columns kung may existing database na"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Check kung existing ang rma_requests table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rma_requests'")
    if cursor.fetchone():
        # Get current columns
        cursor.execute("PRAGMA table_info(rma_requests)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing columns kung wala pa
        missing_columns = {
            'filer_name': 'TEXT',
            'date_filled': 'TEXT',
            'product': 'TEXT',
            'attachments': 'TEXT',
            'authorizer_attachments': 'TEXT',
            'approver_attachments': 'TEXT'
        }
        
        for col_name, col_type in missing_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(f'ALTER TABLE rma_requests ADD COLUMN {col_name} {col_type}')
                    print(f"✅ Added missing column: {col_name}")
                except Exception as e:
                    print(f"⚠️ Error adding column {col_name}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Migration check completed!")

def drop_all_tables():
    """I-drop lahat ng tables"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    tables = ['notifications', 'rma_requests', 'dealer_profiles', 'users']
    
    for table in tables:
        cursor.execute(f'DROP TABLE IF EXISTS {table}')
        print(f"✅ Dropped table: {table}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ All tables dropped!")

def reset_database():
    """I-reset ang buong database"""
    drop_all_tables()
    init_db()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset":
            reset_database()
        elif sys.argv[1] == "migrate":
            migrate_existing_database()
        else:
            print("Usage: python db.py [reset|migrate]")
    else:
        init_db()
        migrate_existing_database()