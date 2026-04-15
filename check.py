from database.db import get_db_connection

def recreate_all_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🔄 RECREATING ALL TABLES")
    print("=" * 60)
    
    # Drop existing tables (order matters due to foreign keys)
    print("\n🗑️ Dropping existing tables...")
    
    cursor.execute("DROP TABLE IF EXISTS rma_requests")
    print("   ✓ rma_requests dropped")
    
    cursor.execute("DROP TABLE IF EXISTS notifications")
    print("   ✓ notifications dropped")
    
    cursor.execute("DROP TABLE IF EXISTS dealer_profiles")
    print("   ✓ dealer_profiles dropped")
    
    cursor.execute("DROP TABLE IF EXISTS users")
    print("   ✓ users dropped")
    
    cursor.execute("DROP TABLE IF EXISTS sqlite_sequence")
    print("   ✓ sqlite_sequence dropped")
    
    # Create users table
    print("\n📝 Creating users table...")
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT,
            contact_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("   ✓ users table created")
    
    # Create dealer_profiles table
    print("\n📝 Creating dealer_profiles table...")
    cursor.execute('''
        CREATE TABLE dealer_profiles (
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
    print("   ✓ dealer_profiles table created")
    
    # Create rma_requests table (COMPLETE with all 38 columns)
    print("\n📝 Creating rma_requests table with 38 columns...")
    cursor.execute('''
        CREATE TABLE rma_requests (
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
            status TEXT DEFAULT 'pending_dealer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            authorizer_attachments TEXT,
            approver_attachments TEXT,
            FOREIGN KEY (dealer_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    print("   ✓ rma_requests table created (38 columns)")
    
    # Create notifications table
    print("\n📝 Creating notifications table...")
    cursor.execute('''
        CREATE TABLE notifications (
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
    print("   ✓ notifications table created")
    
    conn.commit()
    
    # Verify all tables are created
    print("\n" + "=" * 60)
    print("✅ VERIFICATION")
    print("=" * 60)
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("\n📋 Tables created:")
    for table in tables:
        print(f"   - {table['name']}")
    
    # Verify rma_requests columns
    print("\n📋 rma_requests columns:")
    cursor.execute("PRAGMA table_info(rma_requests)")
    columns = cursor.fetchall()
    
    expected_columns = [
        'id', 'rma_number', 'dealer_id', 'return_type', 'reason_for_return',
        'warranty', 'filer_name', 'distributor_name', 'date_filled', 'product',
        'product_description', 'work_environment', 'po_number', 'sales_invoice_number',
        'shipping_date', 'return_date', 'end_user_company', 'end_user_location',
        'end_user_industry', 'end_user_contact_person', 'problem_description',
        'dealer_comments', 'authorized_by', 'authorized_date', 'return_received_by',
        'authorizer_comments', 'approved_by', 'approved_date', 'approved_with',
        'replacement_order_no', 'closed_date', 'approver_comments', 'attachments',
        'status', 'created_at', 'updated_at', 'authorizer_attachments', 'approver_attachments'
    ]
    
    for col in columns:
        if col['name'] in expected_columns:
            print(f"   ✅ {col['name']} : {col['type']}")
        else:
            print(f"   ⚠️ {col['name']} : {col['type']}")
    
    print(f"\n📊 Total columns: {len(columns)}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 ALL TABLES RECREATED SUCCESSFULLY!")
    print("=" * 60)
    print("\n⚠️ Note: All data has been deleted.")
    print("   Database structure is fresh and ready.")

def recreate_only_rma_table():
    """Alternative: Recreate only rma_requests table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🔄 RECREATING ONLY rma_requests TABLE")
    print("=" * 60)
    
    # Drop only rma_requests
    print("\n🗑️ Dropping rma_requests table...")
    cursor.execute("DROP TABLE IF EXISTS rma_requests")
    print("   ✓ rma_requests dropped")
    
    # Drop notifications (depends on rma_requests)
    cursor.execute("DROP TABLE IF EXISTS notifications")
    print("   ✓ notifications dropped")
    
    # Recreate rma_requests
    print("\n📝 Creating rma_requests table...")
    cursor.execute('''
        CREATE TABLE rma_requests (
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
            status TEXT DEFAULT 'pending_dealer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            authorizer_attachments TEXT,
            approver_attachments TEXT,
            FOREIGN KEY (dealer_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    print("   ✓ rma_requests table recreated")
    
    # Recreate notifications
    print("\n📝 Recreating notifications table...")
    cursor.execute('''
        CREATE TABLE notifications (
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
    print("   ✓ notifications table recreated")
    
    conn.commit()
    
    # Verify
    cursor.execute("PRAGMA table_info(rma_requests)")
    columns = cursor.fetchall()
    
    print(f"\n✅ rma_requests recreated with {len(columns)} columns")
    
    conn.close()
    
    print("\n🎉 rma_requests table recreated successfully!")

if __name__ == '__main__':
    print("\n⚠️  WARNING: This will DELETE ALL DATA and RECREATE tables!")
    print("   Database structure will be fresh.\n")
    
    print("Options:")
    print("   1 - Recreate ALL tables (users, profiles, rma, notifications)")
    print("   2 - Recreate ONLY rma_requests table")
    print("   3 - Cancel")
    
    choice = input("\nEnter choice (1, 2, or 3): ")
    
    if choice == '1':
        confirm = input("\nType 'RECREATE ALL' to confirm: ")
        if confirm == 'RECREATE ALL':
            recreate_all_tables()
        else:
            print("\n❌ Cancelled.")
    elif choice == '2':
        confirm = input("\nType 'RECREATE RMA' to confirm: ")
        if confirm == 'RECREATE RMA':
            recreate_only_rma_table()
        else:
            print("\n❌ Cancelled.")
    else:
        print("\n❌ Cancelled.")