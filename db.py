from dotenv import load_dotenv
import os
from mysql.connector import pooling

# Load .env variables
load_dotenv()

def _env_first(*names, default=None):
    """Return first non-empty env var among names."""
    for n in names:
        v = os.getenv(n)
        if v is not None and str(v).strip() != "":
            return v
    return default

DB_CONFIG = {
    # PythonAnywhere / eigenes .env kann verschiedene Namen haben -> wir unterstützen mehrere
    "host": _env_first("DB_HOST", default="localhost"),
    "user": _env_first("DB_USER", "MYSQL_USER"),
    "password": _env_first("DB_PASSWORD", "MYSQL_PASSWORD"),
    "database": _env_first("DB_DATABASE", "DB_NAME", "MYSQL_DATABASE"),
    "port": int(_env_first("DB_PORT", default="3306")),
}

# Optional: falls ihr mal SSL/andere Optionen braucht, könnt ihr hier DB_CONFIG erweitern.

# Connection pool (robust initialisieren)
pool = pooling.MySQLConnectionPool(
    pool_name="pool",
    pool_size=5,
    pool_reset_session=True,
    **DB_CONFIG
)

def get_conn():
    """Get a connection from the pool."""
    return pool.get_connection()

def db_read(sql: str, params=None):
    """
    Run SELECT and return list of dict rows.
    Wichtig: dictionary=True damit Templates wie row['name'] funktionieren.
    """
    conn = get_conn()
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        return rows
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def db_write(sql: str, params=None):
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
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
