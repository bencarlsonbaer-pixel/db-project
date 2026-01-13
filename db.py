from dotenv import load_dotenv
import os
from mysql.connector import pooling

# Load .env variables
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE"),
}

# Init db connection pool
pool = pooling.MySQLConnectionPool(pool_name="pool", pool_size=5, **DB_CONFIG)


def get_conn():
    """Get a connection from the pool."""
    return pool.get_connection()


def db_read(sql, params=None):
    """Run a SELECT query and return rows as list of dicts."""
    conn = get_conn()
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return cur.fetchall()
    finally:
        try:
            if cur:
                cur.close()
        except:
            pass
        conn.close()


def db_write(sql, params=None):
    """Run INSERT/UPDATE/DELETE and commit."""
    conn = get_conn()
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
    finally:
        try:
            if cur:
                cur.close()
        except:
            pass
        conn.close()