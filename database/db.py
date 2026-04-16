import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config

def get_db_connection():
    """Create database connection - auto-detect SQLite or PostgreSQL"""
    try:
        if Config.USE_POSTGRES:
            # PostgreSQL for production
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(Config.DATABASE_URL)
            # This makes rows return as dictionaries
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            return conn
        else:
            # SQLite for local development
            import sqlite3
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

def get_placeholder():
    """Return the correct placeholder for the current database"""
    return '%s' if Config.USE_POSTGRES else '?'

def init_db():
    """Initialize all tables - auto-detect SQLite or PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    if Config.USE_POSTGRES:
        # ========== POSTGRESQL SCHEMA ==========
        print("📦 Creating PostgreSQL schema...")
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                contact_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Dealer profiles with region and province
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dealer_profiles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE,
                company_name TEXT,
                region TEXT,
                province TEXT,
                city TEXT,
                barangay TEXT,
                is_approved INTEGER DEFAULT 0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # RMA Requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rma_requests (
                id SERIAL PRIMARY KEY,
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
                attachments TEXT,
                authorized_by INTEGER,
                authorized_date TEXT,
                return_received_by TEXT,
                authorizer_comments TEXT,
                authorizer_attachments TEXT,
                approved_by INTEGER,
                approved_date TEXT,
                approved_with TEXT,
                replacement_order_no TEXT,
                closed_date TEXT,
                approver_comments TEXT,
                approver_attachments TEXT,
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
                id SERIAL PRIMARY KEY,
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
        
        # Add missing columns for existing databases
        try:
            cursor.execute("ALTER TABLE dealer_profiles ADD COLUMN region TEXT")
            print("✅ Added region column")
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE dealer_profiles ADD COLUMN province TEXT")
            print("✅ Added province column")
        except:
            pass
        
        # Indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dealer_profiles_user_id ON dealer_profiles(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dealer_profiles_is_approved ON dealer_profiles(is_approved)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rma_dealer_id ON rma_requests(dealer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rma_status ON rma_requests(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rma_rma_number ON rma_requests(rma_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)')
        
        # Trigger for updated_at
        cursor.execute('''
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        ''')
        
        cursor.execute('''
            DROP TRIGGER IF EXISTS update_rma_requests_timestamp ON rma_requests;
            CREATE TRIGGER update_rma_requests_timestamp
            BEFORE UPDATE ON rma_requests
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ''')
        
        print("✅ PostgreSQL database tables created successfully!")
        
    else:
        # ========== SQLITE SCHEMA ==========
        print("📦 Creating SQLite schema...")
        
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
        
        # Dealer profiles with region and province
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dealer_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                company_name TEXT,
                region TEXT,
                province TEXT,
                city TEXT,
                barangay TEXT,
                is_approved INTEGER DEFAULT 0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
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
                attachments TEXT,
                authorized_by INTEGER,
                authorized_date TEXT,
                return_received_by TEXT,
                authorizer_comments TEXT,
                authorizer_attachments TEXT,
                approved_by INTEGER,
                approved_date TEXT,
                approved_with TEXT,
                replacement_order_no TEXT,
                closed_date TEXT,
                approver_comments TEXT,
                approver_attachments TEXT,
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
        
        # Add missing columns for existing databases
        try:
            cursor.execute("ALTER TABLE dealer_profiles ADD COLUMN region TEXT")
            print("✅ Added region column")
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE dealer_profiles ADD COLUMN province TEXT")
            print("✅ Added province column")
        except:
            pass
        
        # Indexes for SQLite
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dealer_profiles_user_id ON dealer_profiles(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dealer_profiles_is_approved ON dealer_profiles(is_approved)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rma_dealer_id ON rma_requests(dealer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rma_status ON rma_requests(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rma_rma_number ON rma_requests(rma_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)')
        
        # Trigger for updated_at (SQLite)
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_rma_requests_timestamp 
            AFTER UPDATE ON rma_requests
            BEGIN
                UPDATE rma_requests SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        ''')
        
        print("✅ SQLite database tables created successfully!")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Indexes and triggers added for performance!")

def drop_all_tables():
    """Drop all tables"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    if Config.USE_POSTGRES:
        cursor.execute('DROP TABLE IF EXISTS notifications CASCADE')
        cursor.execute('DROP TABLE IF EXISTS rma_requests CASCADE')
        cursor.execute('DROP TABLE IF EXISTS dealer_profiles CASCADE')
        cursor.execute('DROP TABLE IF EXISTS users CASCADE')
    else:
        cursor.execute('DROP TABLE IF EXISTS notifications')
        cursor.execute('DROP TABLE IF EXISTS rma_requests')
        cursor.execute('DROP TABLE IF EXISTS dealer_profiles')
        cursor.execute('DROP TABLE IF EXISTS users')
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ All tables dropped!")

def reset_database():
    """Reset the entire database"""
    drop_all_tables()
    init_db()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset":
            reset_database()
        else:
            print("Usage: python db.py [reset]")
    else:
        init_db()