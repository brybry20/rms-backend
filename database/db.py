import os
import sqlite3
import psycopg2
import psycopg2.extras

def get_db_connection():
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