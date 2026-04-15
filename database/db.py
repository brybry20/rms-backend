import os
import sqlite3
import psycopg2
import psycopg2.extras

def get_db_connection():
    """Create database connection for both SQLite (local) and PostgreSQL (production)"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Production: PostgreSQL
        conn = psycopg2.connect(database_url)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    else:
        # Development: SQLite
        conn = sqlite3.connect('rma.db')
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Initialize database tables - creates all necessary tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
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
    
    # Create dealer_profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dealer_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE,
            company_name TEXT,
            city TEXT,
            barangay TEXT,
            is_approved INTEGER DEFAULT 0,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create rma_requests table
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
    
    # Create notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            message TEXT,
            type TEXT,
            is_read INTEGER DEFAULT 0,
            related_rma_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database tables created successfully!")