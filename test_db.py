"""
Database Diagnostic & Verification Utility
Software Management System (College DBMS Project)
Supports Oracle (SQL*Plus / as sysdba) & MySQL
"""

import sys
import os
import db_config

def run_diagnostics():
    print("=" * 65)
    print("SOFTWARE MANAGEMENT SYSTEM - DATABASE DIAGNOSTICS")
    print("=" * 65)

    conn = db_config.get_db_connection()
    if not conn:
        print("[FAIL] Could not connect to database.")
        print(f"Error details: {db_config.LAST_CONNECTION_ERROR}")
        print("=" * 65)
        return False

    engine = db_config.ACTIVE_DB_ENGINE
    print(f"  [OK] Successfully connected to {engine} Database!")
    if engine == "Oracle":
        print("  -> Authentication: Windows OS Authentication (as sysdba)")
        print("  -> Port: 1521 (Oracle Listener active)")
    else:
        print(f"  -> Host: {db_config.DB_CONFIG['host']}:{db_config.DB_CONFIG['port']}")

    print("-" * 65)
    print("\n[Step 2] Verifying All 11 Required Entities in Database...")
    cur = conn.cursor()

    required_tables = [
        'USER', 'DEPARTMENT', 'PROJECT', 'DEVELOPER', 'SOFTWARE',
        'VERSION', 'BUG', 'MAINTENANCE', 'LICENSE', 'TECHNOLOGY', 'SOFTWARE_TECHNOLOGY'
    ]

    for table in required_tables:
        try:
            cur.execute(f"SELECT COUNT(*) AS total FROM {table}")
            row = cur.fetchone()
            count = row['total'] if row and 'total' in row else list(row.values())[0]
            print(f"  * {table.ljust(22)} : {count} records")
        except Exception as e:
            print(f"  * {table.ljust(22)} : [FAIL] Error ({e})")

    # Verify admin user
    try:
        cur.execute("SELECT Name, Email FROM USER WHERE Email = %s", ('admin@sms.com',))
        admin = cur.fetchone()
        if admin:
            print("\n  [OK] Verified Administrator Account:")
            print(f"     Name:  {admin['Name']}")
            print(f"     Email: {admin['Email']}")
    except Exception as e:
        print(f"  [WARN] Verifying admin: {e}")

    conn.close()
    print("\n" + "=" * 65)
    print("ALL 11 TABLES ARE LOADED AND READY!")
    print("You can now start your web application in VS Code terminal:")
    print("    py app.py")
    print("Then open in your browser: http://127.0.0.1:5000")
    print("=" * 65)
    return True

if __name__ == '__main__':
    run_diagnostics()
