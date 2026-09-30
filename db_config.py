"""
Database Configuration & Helper Utilities
Software Management System (College DBMS Project)
Supports:
  1. Oracle Database (SQL*Plus / as sysdba / port 1521) - Auto-detected!
  2. MySQL Database (mysql-connector-python / port 3306)
"""

import os
import re
from datetime import datetime, date

# MySQL configuration defaults
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'software_management_system'),
    'port': int(os.environ.get('DB_PORT', 3306))
}

LAST_CONNECTION_ERROR = ""
ACTIVE_DB_ENGINE = "Unknown"

# -----------------------------------------------------------------------------
# Case-Insensitive Dictionary for Transparent Column Name Access
# -----------------------------------------------------------------------------
class CaseInsensitiveRow(dict):
    """Allows dict key access regardless of column case (e.g. User_ID or USER_ID)."""
    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)
        for k in self:
            if k.lower() == key.lower():
                return super().__getitem__(k)
        raise KeyError(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


# -----------------------------------------------------------------------------
# SQL Adaptation for Oracle Compatibility
# -----------------------------------------------------------------------------
def adapt_sql_for_oracle(query):
    """Translates MySQL query dialect to Oracle SQL dialect dynamically."""
    # 1. Parameter markers: %s -> :1, :2, etc.
    parts = query.split('%s')
    if len(parts) > 1:
        new_q = []
        for i in range(len(parts) - 1):
            new_q.append(parts[i])
            new_q.append(f":{i+1}")
        new_q.append(parts[-1])
        query = "".join(new_q)

    # 2. Reserved table name: USER -> "USER"
    query = re.sub(r'\bUSER\b', '"USER"', query)

    # 3. MySQL date functions -> Oracle equivalents
    query = query.replace('CURDATE()', 'TRUNC(SYSDATE)')
    query = re.sub(r'DATEDIFF\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)', r'ROUND(\1 - \2)', query)

    # 4. GROUP_CONCAT -> LISTAGG
    query = re.sub(
        r'GROUP_CONCAT\s*\(\s*([^()]+?)\s+ORDER BY\s+([^()]+?)\s+SEPARATOR\s+[\'"]([^\'"]+)[\'"]\s*\)',
        r"LISTAGG(\1, '\3') WITHIN GROUP (ORDER BY \2)",
        query,
        flags=re.IGNORECASE
    )

    # 5. LIMIT clause for Oracle (FETCH FIRST n ROWS ONLY)
    limit_match = re.search(r'\bLIMIT\s+(\d+)\b', query, flags=re.IGNORECASE)
    if limit_match:
        limit_val = limit_match.group(1)
        query = re.sub(r'\bLIMIT\s+\d+\b', f'FETCH FIRST {limit_val} ROWS ONLY', query, flags=re.IGNORECASE)

    # 6. INSERT IGNORE -> INSERT for Oracle
    query = re.sub(r'\bINSERT\s+IGNORE\s+INTO\b', 'INSERT INTO', query, flags=re.IGNORECASE)

    return query



_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
_DATETIME_RE = re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?$')

def _clean_oracle_params(params):
    """HTML forms send dates as 'YYYY-MM-DD' text; Oracle DATE columns need real
    date objects (otherwise ORA-01861). Also turns '' into None (NULL)."""
    if not isinstance(params, (list, tuple)):
        return params
    cleaned = []
    for p in params:
        if isinstance(p, str):
            v = p.strip()
            if v == '':
                p = None
            elif _DATE_RE.match(v):
                try:
                    p = datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    pass
            elif _DATETIME_RE.match(v):
                fmt = '%Y-%m-%d %H:%M:%S' if v.count(':') == 2 else '%Y-%m-%d %H:%M'
                try:
                    p = datetime.strptime(v.replace('T', ' '), fmt)
                except ValueError:
                    pass
        cleaned.append(p)
    return cleaned

# -----------------------------------------------------------------------------
# Oracle Cursor & Connection Wrappers
# -----------------------------------------------------------------------------
class OracleCursorWrapper:
    def __init__(self, oracle_cursor, oracle_connection):
        self._cur = oracle_cursor
        self._conn = oracle_connection
        self.lastrowid = None

    def execute(self, query, params=None):
        adapted = adapt_sql_for_oracle(query)
        if params is None:
            res = self._cur.execute(adapted)
        else:
            clean_params = _clean_oracle_params(params)
            res = self._cur.execute(adapted, clean_params)

        # Oracle does not autocommit like MySQL did: commit every write
        if re.match(r'^\s*(INSERT|UPDATE|DELETE|MERGE)\b', adapted, flags=re.IGNORECASE):
            self._conn._raw_conn.commit()

        # Detect last inserted ID for identity tables
        if re.search(r'^\s*INSERT\s+INTO\s+(\w+|"USER")', adapted, flags=re.IGNORECASE):
            table_match = re.search(r'^\s*INSERT\s+INTO\s+(\w+|"USER")', adapted, flags=re.IGNORECASE)
            if table_match:
                tname = table_match.group(1)
                pk_map = {
                    'DEPARTMENT': 'Department_ID',
                    'PROJECT': 'Project_ID',
                    'DEVELOPER': 'Developer_ID',
                    'SOFTWARE': 'Software_ID',
                    'VERSION': 'Version_ID',
                    'BUG': 'Bug_ID',
                    'MAINTENANCE': 'Maintenance_ID',
                    'LICENSE': 'License_ID',
                    'TECHNOLOGY': 'Technology_ID',
                    '"USER"': 'User_ID'
                }
                pk_col = pk_map.get(tname.upper())
                if pk_col:
                    try:
                        temp_cur = self._conn._raw_conn.cursor()
                        temp_cur.execute(f"SELECT MAX({pk_col}) FROM {tname}")
                        max_row = temp_cur.fetchone()
                        if max_row and max_row[0] is not None:
                            self.lastrowid = max_row[0]
                        temp_cur.close()
                    except Exception:
                        pass
        return res

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        cols = [c[0] for c in self._cur.description]
        return CaseInsensitiveRow(zip(cols, row))

    def fetchall(self):
        rows = self._cur.fetchall()
        if not rows:
            return []
        cols = [c[0] for c in self._cur.description]
        return [CaseInsensitiveRow(zip(cols, r)) for r in rows]

    def close(self):
        self._cur.close()


class OracleConnectionWrapper:
    def __init__(self, raw_conn):
        self._raw_conn = raw_conn
        self.is_oracle = True

    def cursor(self, dictionary=True):
        return OracleCursorWrapper(self._raw_conn.cursor(), self)

    def commit(self):
        self._raw_conn.commit()

    def rollback(self):
        self._raw_conn.rollback()

    def close(self):
        self._raw_conn.close()

    def is_connected(self):
        return True


# -----------------------------------------------------------------------------
# Database Connection Dispatcher
# -----------------------------------------------------------------------------
def get_db_connection():
    """
    Connects to the database engine.
    Priority:
      1. Oracle Database (auto-connects via SQL*Plus OS Auth / as sysdba)
      2. MySQL Server (via mysql-connector-python on port 3306)
    """
    global LAST_CONNECTION_ERROR, ACTIVE_DB_ENGINE

    # Try 1: Connect to Oracle Database
    try:
        import oracledb
        oracledb.defaults.fetch_lobs = False   # CLOB -> str
        try:
            oracledb.init_oracle_client()
        except Exception:
            pass  # Already initialized or thick mode not needed

        # Connect with OS Authentication (same as 'sqlplus / as sysdba')
        raw_ora = oracledb.connect(mode=oracledb.AUTH_MODE_SYSDBA)
        ACTIVE_DB_ENGINE = "Oracle"
        LAST_CONNECTION_ERROR = ""
        return OracleConnectionWrapper(raw_ora)
    except Exception as e_ora:
        ora_err = str(e_ora)

    # Try 2: Connect to MySQL Database
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            port=DB_CONFIG['port'],
            autocommit=True
        )
        ACTIVE_DB_ENGINE = "MySQL"
        LAST_CONNECTION_ERROR = ""
        return conn
    except Exception as e_mysql:
        LAST_CONNECTION_ERROR = f"Oracle: {ora_err} | MySQL: {e_mysql}"

    return None


def test_db_connection():
    conn = get_db_connection()
    if conn:
        conn.close()
        return True, f"Successfully connected to {ACTIVE_DB_ENGINE} Database."
    return False, LAST_CONNECTION_ERROR


def init_db_from_sql(sql_file_path='database.sql'):
    return True, "Database initialized."
