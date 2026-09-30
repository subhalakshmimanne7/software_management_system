"""
SOFTWARE MANAGEMENT SYSTEM
College DBMS Project - 2nd Year CSE
Backend: Python Flask
Database: MySQL
Connector: mysql-connector-python
"""

import os
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error as _MySQLError
try:
    import oracledb
    Error = (_MySQLError, oracledb.Error)
except ImportError:
    Error = _MySQLError

import db_config
from db_config import get_db_connection, test_db_connection, init_db_from_sql, DB_CONFIG

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sms_college_project_secret_key_2025')


# ---------------------------------------------------------------------
# Helper Decorator: Login Required
# ---------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first to access the Software Management System.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------------------------
# Context Processor: Inject Current Date and User into All Templates
# ---------------------------------------------------------------------
@app.context_processor
def inject_globals():
    return {
        'current_year': datetime.now().year,
        'today_date': date.today().isoformat(),
        'logged_user_name': session.get('user_name', 'Guest'),
        'logged_user_email': session.get('user_email', '')
    }


# ---------------------------------------------------------------------
# Route: System Diagnostics / DB Initializer
# ---------------------------------------------------------------------
@app.route('/init-db', methods=['GET', 'POST'])
def initialize_database():
    """Provides a one-click database initialisation option."""
    success, message = init_db_from_sql('database.sql')
    if success:
        flash(message, 'success')
    else:
        flash(f"Error: {message}", 'danger')
    return redirect(url_for('dashboard'))


# ---------------------------------------------------------------------
# Authentication Routes: Login, Register, Logout
# ---------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Please enter both Email and Password.', 'danger')
            return render_template('login.html', email=email)

        conn = get_db_connection()
        if not conn:
            err_msg = db_config.LAST_CONNECTION_ERROR or "Please verify MySQL server is running on localhost:3306."
            flash(f'Database Connection Failed: {err_msg}', 'danger')
            return render_template('login.html', email=email)

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM USER WHERE Email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                # Support both hashed passwords and legacy plain text fallback for convenience
                is_valid = False
                stored_pwd = user['Password']
                if stored_pwd.startswith('scrypt:') or stored_pwd.startswith('pbkdf2:'):
                    is_valid = check_password_hash(stored_pwd, password)
                else:
                    is_valid = (stored_pwd == password)

                if is_valid:
                    session['user_id'] = user['User_ID']
                    session['user_name'] = user['Name']
                    session['user_email'] = user['Email']
                    flash(f"Welcome back, {user['Name']}!", 'success')
                    return redirect(url_for('dashboard'))

            flash('Invalid email or password. Please try again.', 'danger')
        except Error as e:
            flash(f"Database query error: {e}", 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', name=name, email=email)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html', name=name, email=email)

        conn = get_db_connection()
        if not conn:
            flash('Database connection failed. Please ensure MySQL is running.', 'danger')
            return render_template('register.html')

        try:
            cursor = conn.cursor(dictionary=True)
            # Check unique email constraint
            cursor.execute("SELECT User_ID FROM USER WHERE Email = %s", (email,))
            if cursor.fetchone():
                flash('An account with this email already exists. Please log in.', 'warning')
                cursor.close()
                conn.close()
                return redirect(url_for('login'))

            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO USER (Name, Email, Password) VALUES (%s, %s, %s)",
                (name, email, hashed_password)
            )
            cursor.close()
            conn.close()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Error as e:
            flash(f"Database error during registration: {e}", 'danger')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('login'))


# ---------------------------------------------------------------------
# Dashboard Route
# ---------------------------------------------------------------------
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response


DASHBOARD_TABLES = {
    'departments': 'DEPARTMENT', 'projects': 'PROJECT', 'developers': 'DEVELOPER',
    'software': 'SOFTWARE', 'versions': 'VERSION', 'technologies': 'TECHNOLOGY',
    'licenses': 'LICENSE', 'bugs': 'BUG', 'maintenance': 'MAINTENANCE', 'users': 'USER',
}


DASHBOARD_ENTITIES = {
    'departments': {
        'title': 'Departments', 'icon': '🏢', 'count_key': 'departments', 'page': 'departments',
        'sql': """SELECT Department_ID, Department_Name, Location, Contact_Email, Description
                  FROM DEPARTMENT ORDER BY Department_ID""",
        'cols': [('Department_ID', 'ID'), ('Department_Name', 'Department'), ('Location', 'Location'),
                 ('Contact_Email', 'Contact Email'), ('Description', 'Description')],
    },
    'projects': {
        'title': 'Projects', 'icon': '📁', 'count_key': 'projects', 'page': 'projects',
        'sql': """SELECT p.Project_ID, p.Project_Name, d.Department_Name, p.Project_Status,
                         p.Start_Date, p.End_Date
                  FROM PROJECT p INNER JOIN DEPARTMENT d ON p.Department_ID = d.Department_ID
                  ORDER BY p.Project_ID""",
        'cols': [('Project_ID', 'ID'), ('Project_Name', 'Project'), ('Department_Name', 'Department'),
                 ('Project_Status', 'Status'), ('Start_Date', 'Start'), ('End_Date', 'End')],
    },
    'developers': {
        'title': 'Developers', 'icon': '👨‍💻', 'count_key': 'developers', 'page': 'developers',
        'sql': """SELECT dev.Developer_ID, dev.Developer_Name, dev.Email, d.Department_Name
                  FROM DEVELOPER dev INNER JOIN DEPARTMENT d ON dev.Department_ID = d.Department_ID
                  ORDER BY dev.Developer_ID""",
        'cols': [('Developer_ID', 'ID'), ('Developer_Name', 'Developer'), ('Email', 'Email'),
                 ('Department_Name', 'Department')],
    },
    'software': {
        'title': 'Software', 'icon': '💻', 'count_key': 'software', 'page': 'software',
        'sql': """SELECT s.Software_ID, s.Software_Name, p.Project_Name, s.Status, s.Description
                  FROM SOFTWARE s INNER JOIN PROJECT p ON s.Project_ID = p.Project_ID
                  ORDER BY s.Software_ID""",
        'cols': [('Software_ID', 'ID'), ('Software_Name', 'Software'), ('Project_Name', 'Project'),
                 ('Status', 'Status'), ('Description', 'Description')],
    },
    'versions': {
        'title': 'Versions', 'icon': '🏷️', 'count_key': 'versions', 'page': 'versions',
        'sql': """SELECT v.Version_ID, s.Software_Name, v.Version_Number, v.Release_Date
                  FROM VERSION v INNER JOIN SOFTWARE s ON v.Software_ID = s.Software_ID
                  ORDER BY v.Release_Date DESC""",
        'cols': [('Version_ID', 'ID'), ('Software_Name', 'Software'), ('Version_Number', 'Version'),
                 ('Release_Date', 'Release Date')],
    },
    'technologies': {
        'title': 'Technologies', 'icon': '⚙️', 'count_key': 'technologies', 'page': 'technologies',
        'sql': """SELECT Technology_ID, Technology_Name, Technology_Type, Version, Description
                  FROM TECHNOLOGY ORDER BY Technology_ID""",
        'cols': [('Technology_ID', 'ID'), ('Technology_Name', 'Technology'), ('Technology_Type', 'Type'),
                 ('Version', 'Version'), ('Description', 'Description')],
    },
    'licenses': {
        'title': 'Licenses', 'icon': '📜', 'count_key': 'licenses', 'page': 'licenses',
        'sql': """SELECT l.License_ID, s.Software_Name, l.License_Type, l.Start_Date,
                         l.Expiry_Date, l.License_Status
                  FROM LICENSE l INNER JOIN SOFTWARE s ON l.Software_ID = s.Software_ID
                  ORDER BY l.License_ID""",
        'cols': [('License_ID', 'ID'), ('Software_Name', 'Software'), ('License_Type', 'Type'),
                 ('Start_Date', 'Start'), ('Expiry_Date', 'Expiry'), ('License_Status', 'Status')],
    },
    'bugs': {
        'title': 'Bugs', 'icon': '🐞', 'count_key': 'bugs', 'page': 'bugs',
        'sql': """SELECT b.Bug_ID, s.Software_Name, b.Description, b.Severity, b.Status, b.Reported_Date
                  FROM BUG b INNER JOIN SOFTWARE s ON b.Software_ID = s.Software_ID
                  ORDER BY b.Bug_ID""",
        'cols': [('Bug_ID', 'ID'), ('Software_Name', 'Software'), ('Description', 'Description'),
                 ('Severity', 'Severity'), ('Status', 'Status'), ('Reported_Date', 'Reported')],
    },
    'maintenance': {
        'title': 'Maintenance', 'icon': '🛠️', 'count_key': 'maintenance', 'page': 'maintenance',
        'sql': """SELECT m.Maintenance_ID, m.Maintenance_Date, dev.Developer_Name, m.Description, m.Status
                  FROM MAINTENANCE m INNER JOIN DEVELOPER dev ON m.Performed_By = dev.Developer_ID
                  ORDER BY m.Maintenance_Date DESC""",
        'cols': [('Maintenance_ID', 'ID'), ('Maintenance_Date', 'Date'), ('Developer_Name', 'Developer'),
                 ('Description', 'Action'), ('Status', 'Status')],
    },
    'users': {
        'title': 'Users', 'icon': '👥', 'count_key': 'users', 'page': 'users',
        'sql': """SELECT User_ID, Name, Email FROM USER ORDER BY User_ID""",
        'cols': [('User_ID', 'ID'), ('Name', 'Name'), ('Email', 'Email')],
    },
}


def _empty_dashboard(selected='overview'):
    return render_template(
        'dashboard.html', counts={}, active_projects=[], active_software=[], open_bugs=[],
        expired_licenses=[], recent_maintenance=[], db_connected=False,
        selected=selected, entity_menu=[], entity=None, entity_rows=[]
    )


@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    selected = request.args.get('entity', 'overview').strip().lower()
    if selected != 'overview' and selected not in DASHBOARD_ENTITIES:
        selected = 'overview'

    conn = get_db_connection()
    if not conn:
        flash('Unable to connect to the database. Please verify your database server status and configuration.', 'danger')
        return _empty_dashboard(selected)

    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Counts for the left panel and stat cards
        counts = {}
        for key, cfg in DASHBOARD_ENTITIES.items():
            table = DASHBOARD_TABLES[key]
            cursor.execute(f"SELECT COUNT(*) AS total FROM {table}")
            row = cursor.fetchone()
            counts[key] = row['total'] if row else 0

        entity_menu = [
            {'key': k, 'title': c['title'], 'icon': c['icon'], 'count': counts.get(k, 0)}
            for k, c in DASHBOARD_ENTITIES.items()
        ]

        active_projects = active_software = open_bugs = expired_licenses = recent_maintenance = []
        entity = None
        entity_rows = []

        if selected == 'overview':
            cursor.execute("""
                SELECT p.Project_ID, p.Project_Name, p.Project_Status, p.Start_Date, p.End_Date, d.Department_Name
                FROM PROJECT p
                INNER JOIN DEPARTMENT d ON p.Department_ID = d.Department_ID
                WHERE p.Project_Status <> 'Completed'
                ORDER BY p.Project_ID DESC LIMIT 8
            """)
            active_projects = cursor.fetchall()

            cursor.execute("""
                SELECT b.Bug_ID, b.Description, b.Severity, b.Status, b.Reported_Date, s.Software_Name
                FROM BUG b
                INNER JOIN SOFTWARE s ON b.Software_ID = s.Software_ID
                WHERE b.Status IN ('Open', 'In Progress')
                ORDER BY CASE b.Severity
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    ELSE 4 END, b.Bug_ID DESC
                LIMIT 8
            """)
            open_bugs = cursor.fetchall()

            cursor.execute("""
                SELECT l.License_ID, l.License_Type, l.Start_Date, l.Expiry_Date, l.License_Status, s.Software_Name,
                       DATEDIFF(CURDATE(), l.Expiry_Date) AS Days_Expired
                FROM LICENSE l
                INNER JOIN SOFTWARE s ON l.Software_ID = s.Software_ID
                WHERE l.Expiry_Date < CURDATE()
                ORDER BY l.Expiry_Date ASC LIMIT 8
            """)
            expired_licenses = cursor.fetchall()

            cursor.execute("""
                SELECT m.Maintenance_ID, m.Maintenance_Date, m.Description, m.Status,
                       b.Description AS Bug_Description, dev.Developer_Name
                FROM MAINTENANCE m
                INNER JOIN BUG b ON m.Bug_ID = b.Bug_ID
                INNER JOIN DEVELOPER dev ON m.Performed_By = dev.Developer_ID
                ORDER BY m.Maintenance_Date DESC, m.Maintenance_ID DESC LIMIT 8
            """)
            recent_maintenance = cursor.fetchall()
        else:
            entity = dict(DASHBOARD_ENTITIES[selected], key=selected)
            cursor.execute(entity['sql'])
            entity_rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            'dashboard.html',
            counts=counts,
            active_projects=active_projects,
            active_software=active_software,
            open_bugs=open_bugs,
            expired_licenses=expired_licenses,
            recent_maintenance=recent_maintenance,
            db_connected=True,
            selected=selected,
            entity_menu=entity_menu,
            entity=entity,
            entity_rows=entity_rows
        )
    except Exception as e:
        flash(f"Error loading dashboard: {e}", 'danger')
        return _empty_dashboard(selected)


@app.route('/db-status')
@login_required
def db_status():
    """Diagnostic: which database/schema is the app really using, and what is in it."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'connected': False, 'error': db_config.LAST_CONNECTION_ERROR})
    info = {'connected': True, 'engine': db_config.ACTIVE_DB_ENGINE}
    try:
        cur = conn.cursor(dictionary=True)
        if db_config.ACTIVE_DB_ENGINE == 'Oracle':
            cur.execute("SELECT SYS_CONTEXT('USERENV','CURRENT_SCHEMA') AS S FROM DUAL")
        else:
            cur.execute("SELECT DATABASE() AS S")
        info['schema_or_database'] = list(cur.fetchone().values())[0]
        counts = {}
        for t in ['USER', 'DEPARTMENT', 'PROJECT', 'DEVELOPER', 'SOFTWARE', 'VERSION',
                  'BUG', 'MAINTENANCE', 'LICENSE', 'TECHNOLOGY', 'SOFTWARE_TECHNOLOGY']:
            try:
                cur.execute(f"SELECT COUNT(*) AS total FROM {t}")
                counts[t] = list(cur.fetchone().values())[0]
            except Exception as e:
                counts[t] = f'ERROR: {e}'
        info['row_counts'] = counts
        cur.close()
        conn.close()
    except Exception as e:
        info['error'] = str(e)
    return jsonify(info)


# ---------------------------------------------------------------------
# USER MODULE (CRUD + Search)
# ---------------------------------------------------------------------
@app.route('/users')
@login_required
def users():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('users.html', users=[], search=search)

    cursor = conn.cursor(dictionary=True)
    if search:
        query = "SELECT User_ID, Name, Email FROM USER WHERE Name LIKE %s OR Email LIKE %s ORDER BY User_ID DESC"
        param = f"%{search}%"
        cursor.execute(query, (param, param))
    else:
        cursor.execute("SELECT User_ID, Name, Email FROM USER ORDER BY User_ID DESC")
    user_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('users.html', users=user_list, search=search)


@app.route('/users/add', methods=['POST'])
@login_required
def add_user():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    if not name or not email or not password:
        flash('Name, Email, and Password are all required.', 'danger')
        return redirect(url_for('users'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('users'))

    try:
        cursor = conn.cursor()
        hashed = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO USER (Name, Email, Password) VALUES (%s, %s, %s)",
            (name, email, hashed)
        )
        cursor.close()
        conn.close()
        flash(f'User "{name}" created successfully.', 'success')
    except Error as e:
        flash(f'Error adding user: {e}', 'danger')

    return redirect(url_for('users'))


@app.route('/users/edit/<int:id>', methods=['POST'])
@login_required
def edit_user(id):
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    if not name or not email:
        flash('Name and Email cannot be empty.', 'danger')
        return redirect(url_for('users'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('users'))

    try:
        cursor = conn.cursor()
        if password:
            hashed = generate_password_hash(password)
            cursor.execute(
                "UPDATE USER SET Name = %s, Email = %s, Password = %s WHERE User_ID = %s",
                (name, email, hashed, id)
            )
        else:
            cursor.execute(
                "UPDATE USER SET Name = %s, Email = %s WHERE User_ID = %s",
                (name, email, id)
            )
        cursor.close()
        conn.close()
        flash('User details updated successfully.', 'success')
    except Error as e:
        flash(f'Error updating user: {e}', 'danger')

    return redirect(url_for('users'))


@app.route('/users/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if id == session.get('user_id'):
        flash('You cannot delete your own logged-in account!', 'danger')
        return redirect(url_for('users'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('users'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM USER WHERE User_ID = %s", (id,))
        cursor.close()
        conn.close()
        flash('User deleted successfully.', 'success')
    except Error as e:
        flash(f'Error deleting user: {e}', 'danger')

    return redirect(url_for('users'))


# ---------------------------------------------------------------------
# DEPARTMENT MODULE (CRUD + Search)
# ---------------------------------------------------------------------
@app.route('/departments')
@login_required
def departments():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('departments.html', departments=[], search=search)

    cursor = conn.cursor(dictionary=True)
    if search:
        query = """
            SELECT * FROM DEPARTMENT 
            WHERE Department_Name LIKE %s OR Location LIKE %s OR Contact_Email LIKE %s
            ORDER BY Department_ID DESC
        """
        param = f"%{search}%"
        cursor.execute(query, (param, param, param))
    else:
        cursor.execute("SELECT * FROM DEPARTMENT ORDER BY Department_ID DESC")
    dept_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('departments.html', departments=dept_list, search=search)


@app.route('/departments/add', methods=['POST'])
@login_required
def add_department():
    name = request.form.get('department_name', '').strip()
    description = request.form.get('description', '').strip()
    location = request.form.get('location', '').strip()
    contact_email = request.form.get('contact_email', '').strip()

    if not name:
        flash('Department Name is required.', 'danger')
        return redirect(url_for('departments'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('departments'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO DEPARTMENT (Department_Name, Description, Location, Contact_Email) 
               VALUES (%s, %s, %s, %s)""",
            (name, description, location, contact_email)
        )
        cursor.close()
        conn.close()
        flash(f'Department "{name}" added successfully.', 'success')
    except Error as e:
        flash(f'Error adding department: {e}', 'danger')

    return redirect(url_for('departments'))


@app.route('/departments/edit/<int:id>', methods=['POST'])
@login_required
def edit_department(id):
    name = request.form.get('department_name', '').strip()
    description = request.form.get('description', '').strip()
    location = request.form.get('location', '').strip()
    contact_email = request.form.get('contact_email', '').strip()

    if not name:
        flash('Department Name cannot be empty.', 'danger')
        return redirect(url_for('departments'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('departments'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE DEPARTMENT 
               SET Department_Name = %s, Description = %s, Location = %s, Contact_Email = %s 
               WHERE Department_ID = %s""",
            (name, description, location, contact_email, id)
        )
        cursor.close()
        conn.close()
        flash('Department updated successfully.', 'success')
    except Error as e:
        flash(f'Error updating department: {e}', 'danger')

    return redirect(url_for('departments'))


@app.route('/departments/delete/<int:id>', methods=['POST'])
@login_required
def delete_department(id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('departments'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM DEPARTMENT WHERE Department_ID = %s", (id,))
        cursor.close()
        conn.close()
        flash('Department and associated records deleted successfully.', 'success')
    except Error as e:
        flash(f'Error deleting department: {e}', 'danger')

    return redirect(url_for('departments'))


# ---------------------------------------------------------------------
# PROJECT MODULE (CRUD + Search)
# ---------------------------------------------------------------------
@app.route('/projects')
@login_required
def projects():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('projects.html', projects=[], departments=[], search=search)

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Department_ID, Department_Name FROM DEPARTMENT ORDER BY Department_Name ASC")
    departments = cursor.fetchall()

    if search:
        query = """
            SELECT p.*, d.Department_Name 
            FROM PROJECT p
            INNER JOIN DEPARTMENT d ON p.Department_ID = d.Department_ID
            WHERE p.Project_Name LIKE %s OR p.Project_Status LIKE %s OR d.Department_Name LIKE %s
            ORDER BY p.Project_ID DESC
        """
        param = f"%{search}%"
        cursor.execute(query, (param, param, param))
    else:
        query = """
            SELECT p.*, d.Department_Name 
            FROM PROJECT p
            INNER JOIN DEPARTMENT d ON p.Department_ID = d.Department_ID
            ORDER BY p.Project_ID DESC
        """
        cursor.execute(query)
    project_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('projects.html', projects=project_list, departments=departments, search=search)


@app.route('/projects/add', methods=['POST'])
@login_required
def add_project():
    name = request.form.get('project_name', '').strip()
    description = request.form.get('description', '').strip()
    start_date = request.form.get('start_date') or None
    end_date = request.form.get('end_date') or None
    status = request.form.get('project_status', 'Planning').strip()
    dept_id = request.form.get('department_id')

    if not name or not dept_id:
        flash('Project Name and Department are required.', 'danger')
        return redirect(url_for('projects'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('projects'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO PROJECT (Project_Name, Description, Start_Date, End_Date, Project_Status, Department_ID)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (name, description, start_date, end_date, status, dept_id)
        )
        cursor.close()
        conn.close()
        flash(f'Project "{name}" created successfully.', 'success')
    except Error as e:
        flash(f'Error creating project: {e}', 'danger')

    return redirect(url_for('projects'))


@app.route('/projects/edit/<int:id>', methods=['POST'])
@login_required
def edit_project(id):
    name = request.form.get('project_name', '').strip()
    description = request.form.get('description', '').strip()
    start_date = request.form.get('start_date') or None
    end_date = request.form.get('end_date') or None
    status = request.form.get('project_status', 'Planning').strip()
    dept_id = request.form.get('department_id')

    if not name or not dept_id:
        flash('Project Name and Department are required.', 'danger')
        return redirect(url_for('projects'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('projects'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE PROJECT 
               SET Project_Name = %s, Description = %s, Start_Date = %s, End_Date = %s, 
                   Project_Status = %s, Department_ID = %s 
               WHERE Project_ID = %s""",
            (name, description, start_date, end_date, status, dept_id, id)
        )
        cursor.close()
        conn.close()
        flash('Project updated successfully.', 'success')
    except Error as e:
        flash(f'Error updating project: {e}', 'danger')

    return redirect(url_for('projects'))


@app.route('/projects/delete/<int:id>', methods=['POST'])
@login_required
def delete_project(id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('projects'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM PROJECT WHERE Project_ID = %s", (id,))
        cursor.close()
        conn.close()
        flash('Project deleted successfully.', 'success')
    except Error as e:
        flash(f'Error deleting project: {e}', 'danger')

    return redirect(url_for('projects'))


# ---------------------------------------------------------------------
# DEVELOPER MODULE (CRUD + Search)
# ---------------------------------------------------------------------
@app.route('/developers')
@login_required
def developers():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('developers.html', developers=[], departments=[], search=search)

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Department_ID, Department_Name FROM DEPARTMENT ORDER BY Department_Name ASC")
    departments = cursor.fetchall()

    if search:
        query = """
            SELECT dev.*, d.Department_Name 
            FROM DEVELOPER dev
            INNER JOIN DEPARTMENT d ON dev.Department_ID = d.Department_ID
            WHERE dev.Developer_Name LIKE %s OR dev.Email LIKE %s OR d.Department_Name LIKE %s
            ORDER BY dev.Developer_ID DESC
        """
        param = f"%{search}%"
        cursor.execute(query, (param, param, param))
    else:
        query = """
            SELECT dev.*, d.Department_Name 
            FROM DEVELOPER dev
            INNER JOIN DEPARTMENT d ON dev.Department_ID = d.Department_ID
            ORDER BY dev.Developer_ID DESC
        """
        cursor.execute(query)
    dev_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('developers.html', developers=dev_list, departments=departments, search=search)


@app.route('/developers/add', methods=['POST'])
@login_required
def add_developer():
    name = request.form.get('developer_name', '').strip()
    email = request.form.get('email', '').strip()
    dept_id = request.form.get('department_id')

    if not name or not email or not dept_id:
        flash('Developer Name, Email, and Department are required.', 'danger')
        return redirect(url_for('developers'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('developers'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO DEVELOPER (Developer_Name, Email, Department_ID) VALUES (%s, %s, %s)",
            (name, email, dept_id)
        )
        cursor.close()
        conn.close()
        flash(f'Developer "{name}" registered successfully.', 'success')
    except Error as e:
        flash(f'Error registering developer: {e}', 'danger')

    return redirect(url_for('developers'))


@app.route('/developers/edit/<int:id>', methods=['POST'])
@login_required
def edit_developer(id):
    name = request.form.get('developer_name', '').strip()
    email = request.form.get('email', '').strip()
    dept_id = request.form.get('department_id')

    if not name or not email or not dept_id:
        flash('All fields are required.', 'danger')
        return redirect(url_for('developers'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('developers'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE DEVELOPER SET Developer_Name = %s, Email = %s, Department_ID = %s WHERE Developer_ID = %s",
            (name, email, dept_id, id)
        )
        cursor.close()
        conn.close()
        flash('Developer updated successfully.', 'success')
    except Error as e:
        flash(f'Error updating developer: {e}', 'danger')

    return redirect(url_for('developers'))


@app.route('/developers/delete/<int:id>', methods=['POST'])
@login_required
def delete_developer(id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('developers'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM DEVELOPER WHERE Developer_ID = %s", (id,))
        cursor.close()
        conn.close()
        flash('Developer removed successfully.', 'success')
    except Error as e:
        flash(f'Error deleting developer: {e}', 'danger')

    return redirect(url_for('developers'))


# ---------------------------------------------------------------------
# SOFTWARE MODULE (CRUD + Search + M:N Technologies Association)
# ---------------------------------------------------------------------
@app.route('/software')
@login_required
def software():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('software.html', software=[], projects=[], all_technologies=[], search=search)

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Project_ID, Project_Name FROM PROJECT ORDER BY Project_Name ASC")
    projects = cursor.fetchall()

    cursor.execute("SELECT Technology_ID, Technology_Name, Technology_Type FROM TECHNOLOGY ORDER BY Technology_Name ASC")
    all_technologies = cursor.fetchall()

    if search:
        query = """
            SELECT s.*, p.Project_Name
            FROM SOFTWARE s
            INNER JOIN PROJECT p ON s.Project_ID = p.Project_ID
            WHERE s.Software_Name LIKE %s OR s.Status LIKE %s OR p.Project_Name LIKE %s
            ORDER BY s.Software_ID DESC
        """
        param = f"%{search}%"
        cursor.execute(query, (param, param, param))
    else:
        query = """
            SELECT s.*, p.Project_Name
            FROM SOFTWARE s
            INNER JOIN PROJECT p ON s.Project_ID = p.Project_ID
            ORDER BY s.Software_ID DESC
        """
        cursor.execute(query)
    software_list = cursor.fetchall()

    # Fetch associated technologies for each software using SOFTWARE_TECHNOLOGY junction table
    for sw in software_list:
        cursor.execute("""
            SELECT t.Technology_ID, t.Technology_Name, t.Technology_Type
            FROM SOFTWARE_TECHNOLOGY st
            INNER JOIN TECHNOLOGY t ON st.Technology_ID = t.Technology_ID
            WHERE st.Software_ID = %s
            ORDER BY t.Technology_Name ASC
        """, (sw['Software_ID'],))
        sw['technologies'] = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('software.html', software=software_list, projects=projects, all_technologies=all_technologies, search=search)


@app.route('/software/add', methods=['POST'])
@login_required
def add_software():
    name = request.form.get('software_name', '').strip()
    description = request.form.get('description', '').strip()
    status = request.form.get('status', 'Active').strip()
    project_id = request.form.get('project_id')
    selected_technologies = request.form.getlist('technologies')

    if not name or not project_id:
        flash('Software Name and Project are required.', 'danger')
        return redirect(url_for('software'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('software'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO SOFTWARE (Software_Name, Description, Status, Project_ID) VALUES (%s, %s, %s, %s)",
            (name, description, status, project_id)
        )
        new_software_id = cursor.lastrowid

        # Insert selected technologies into SOFTWARE_TECHNOLOGY junction table
        if selected_technologies and new_software_id:
            for tech_id in selected_technologies:
                cursor.execute(
                    "INSERT INTO SOFTWARE_TECHNOLOGY (Software_ID, Technology_ID) VALUES (%s, %s)",
                    (new_software_id, int(tech_id))
                )

        cursor.close()
        conn.close()
        flash(f'Software "{name}" registered successfully with technologies.', 'success')
    except Error as e:
        flash(f'Error registering software: {e}', 'danger')

    return redirect(url_for('software'))


@app.route('/software/edit/<int:id>', methods=['POST'])
@login_required
def edit_software(id):
    name = request.form.get('software_name', '').strip()
    description = request.form.get('description', '').strip()
    status = request.form.get('status', 'Active').strip()
    project_id = request.form.get('project_id')
    selected_technologies = request.form.getlist('technologies')

    if not name or not project_id:
        flash('Software Name and Project are required.', 'danger')
        return redirect(url_for('software'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('software'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE SOFTWARE 
               SET Software_Name = %s, Description = %s, Status = %s, Project_ID = %s 
               WHERE Software_ID = %s""",
            (name, description, status, project_id, id)
        )

        # Update M:N SOFTWARE_TECHNOLOGY mappings
        cursor.execute("DELETE FROM SOFTWARE_TECHNOLOGY WHERE Software_ID = %s", (id,))
        for tech_id in selected_technologies:
            cursor.execute(
                "INSERT INTO SOFTWARE_TECHNOLOGY (Software_ID, Technology_ID) VALUES (%s, %s)",
                (id, int(tech_id))
            )

        cursor.close()
        conn.close()
        flash('Software details updated successfully.', 'success')
    except Error as e:
        flash(f'Error updating software: {e}', 'danger')

    return redirect(url_for('software'))


@app.route('/software/delete/<int:id>', methods=['POST'])
@login_required
def delete_software(id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('software'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM SOFTWARE WHERE Software_ID = %s", (id,))
        cursor.close()
        conn.close()
        flash('Software deleted successfully.', 'success')
    except Error as e:
        flash(f'Error deleting software: {e}', 'danger')

    return redirect(url_for('software'))


@app.route('/software/manage-tech/<int:software_id>', methods=['POST'])
@login_required
def manage_software_tech(software_id):
    """Directly add a technology association via SOFTWARE_TECHNOLOGY."""
    tech_id = request.form.get('technology_id')
    action = request.form.get('action', 'add')

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('software'))

    try:
        cursor = conn.cursor()
        if action == 'add' and tech_id:
            cursor.execute(
                "INSERT IGNORE INTO SOFTWARE_TECHNOLOGY (Software_ID, Technology_ID) VALUES (%s, %s)",
                (software_id, tech_id)
            )
            flash('Technology attached to software successfully.', 'success')
        elif action == 'remove' and tech_id:
            cursor.execute(
                "DELETE FROM SOFTWARE_TECHNOLOGY WHERE Software_ID = %s AND Technology_ID = %s",
                (software_id, tech_id)
            )
            flash('Technology detached from software.', 'info')
        cursor.close()
        conn.close()
    except Error as e:
        flash(f'Error managing software technology: {e}', 'danger')

    return redirect(url_for('software'))


# ---------------------------------------------------------------------
# VERSION MODULE (CRUD + Search)
# ---------------------------------------------------------------------
@app.route('/versions')
@login_required
def versions():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('versions.html', versions=[], software_list=[], search=search)

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Software_ID, Software_Name FROM SOFTWARE ORDER BY Software_Name ASC")
    software_list = cursor.fetchall()

    if search:
        query = """
            SELECT v.*, s.Software_Name 
            FROM VERSION v
            INNER JOIN SOFTWARE s ON v.Software_ID = s.Software_ID
            WHERE v.Version_Number LIKE %s OR s.Software_Name LIKE %s
            ORDER BY v.Version_ID DESC
        """
        param = f"%{search}%"
        cursor.execute(query, (param, param))
    else:
        query = """
            SELECT v.*, s.Software_Name 
            FROM VERSION v
            INNER JOIN SOFTWARE s ON v.Software_ID = s.Software_ID
            ORDER BY v.Version_ID DESC
        """
        cursor.execute(query)
    version_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('versions.html', versions=version_list, software_list=software_list, search=search)


@app.route('/versions/add', methods=['POST'])
@login_required
def add_version():
    software_id = request.form.get('software_id')
    version_number = request.form.get('version_number', '').strip()
    release_date = request.form.get('release_date')

    if not software_id or not version_number or not release_date:
        flash('Software, Version Number, and Release Date are required.', 'danger')
        return redirect(url_for('versions'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('versions'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO VERSION (Software_ID, Version_Number, Release_Date) VALUES (%s, %s, %s)",
            (software_id, version_number, release_date)
        )
        cursor.close()
        conn.close()
        flash(f'Version {version_number} added successfully.', 'success')
    except Error as e:
        flash(f'Error adding version: {e}', 'danger')

    return redirect(url_for('versions'))


@app.route('/versions/edit/<int:id>', methods=['POST'])
@login_required
def edit_version(id):
    software_id = request.form.get('software_id')
    version_number = request.form.get('version_number', '').strip()
    release_date = request.form.get('release_date')

    if not software_id or not version_number or not release_date:
        flash('All fields are required.', 'danger')
        return redirect(url_for('versions'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('versions'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE VERSION 
               SET Software_ID = %s, Version_Number = %s, Release_Date = %s 
               WHERE Version_ID = %s""",
            (software_id, version_number, release_date, id)
        )
        cursor.close()
        conn.close()
        flash('Version updated successfully.', 'success')
    except Error as e:
        flash(f'Error updating version: {e}', 'danger')

    return redirect(url_for('versions'))


@app.route('/versions/delete/<int:id>', methods=['POST'])
@login_required
def delete_version(id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('versions'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM VERSION WHERE Version_ID = %s", (id,))
        cursor.close()
        conn.close()
        flash('Version deleted successfully.', 'success')
    except Error as e:
        flash(f'Error deleting version: {e}', 'danger')

    return redirect(url_for('versions'))


# ---------------------------------------------------------------------
# BUG MODULE (CRUD + Search by status/severity)
# ---------------------------------------------------------------------
@app.route('/bugs')
@login_required
def bugs():
    search = request.args.get('search', '').strip()
    severity_filter = request.args.get('severity', '').strip()
    status_filter = request.args.get('status', '').strip()

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('bugs.html', bugs=[], software_list=[], search=search, severity_filter=severity_filter, status_filter=status_filter)

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Software_ID, Software_Name FROM SOFTWARE ORDER BY Software_Name ASC")
    software_list = cursor.fetchall()

    query = """
        SELECT b.*, s.Software_Name 
        FROM BUG b
        INNER JOIN SOFTWARE s ON b.Software_ID = s.Software_ID
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (b.Description LIKE %s OR s.Software_Name LIKE %s)"
        term = f"%{search}%"
        params.extend([term, term])
    if severity_filter:
        query += " AND b.Severity = %s"
        params.append(severity_filter)
    if status_filter:
        query += " AND b.Status = %s"
        params.append(status_filter)

    query += " ORDER BY b.Bug_ID DESC"
    cursor.execute(query, tuple(params))
    bug_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('bugs.html', bugs=bug_list, software_list=software_list, search=search, severity_filter=severity_filter, status_filter=status_filter)


@app.route('/bugs/add', methods=['POST'])
@login_required
def add_bug():
    software_id = request.form.get('software_id')
    description = request.form.get('description', '').strip()
    severity = request.form.get('severity', 'Medium').strip()
    status = request.form.get('status', 'Open').strip()
    reported_date = request.form.get('reported_date') or date.today().isoformat()

    if not software_id or not description:
        flash('Software and Description are required.', 'danger')
        return redirect(url_for('bugs'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('bugs'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO BUG (Software_ID, Description, Severity, Status, Reported_Date) 
               VALUES (%s, %s, %s, %s, %s)""",
            (software_id, description, severity, status, reported_date)
        )
        cursor.close()
        conn.close()
        flash('Bug ticket reported successfully.', 'success')
    except Error as e:
        flash(f'Error reporting bug: {e}', 'danger')

    return redirect(url_for('bugs'))


@app.route('/bugs/edit/<int:id>', methods=['POST'])
@login_required
def edit_bug(id):
    software_id = request.form.get('software_id')
    description = request.form.get('description', '').strip()
    severity = request.form.get('severity', 'Medium').strip()
    status = request.form.get('status', 'Open').strip()
    reported_date = request.form.get('reported_date')

    if not software_id or not description or not reported_date:
        flash('All fields are required.', 'danger')
        return redirect(url_for('bugs'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('bugs'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE BUG 
               SET Software_ID = %s, Description = %s, Severity = %s, Status = %s, Reported_Date = %s 
               WHERE Bug_ID = %s""",
            (software_id, description, severity, status, reported_date, id)
        )
        cursor.close()
        conn.close()
        flash('Bug updated successfully.', 'success')
    except Error as e:
        flash(f'Error updating bug: {e}', 'danger')

    return redirect(url_for('bugs'))


@app.route('/bugs/delete/<int:id>', methods=['POST'])
@login_required
def delete_bug(id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('bugs'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM BUG WHERE Bug_ID = %s", (id,))
        cursor.close()
        conn.close()
        flash('Bug record deleted successfully.', 'success')
    except Error as e:
        flash(f'Error deleting bug: {e}', 'danger')

    return redirect(url_for('bugs'))


# ---------------------------------------------------------------------
# MAINTENANCE MODULE (CRUD + Search)
# ---------------------------------------------------------------------
@app.route('/maintenance')
@login_required
def maintenance():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('maintenance.html', maintenance_list=[], bugs=[], developers=[], search=search)

    cursor = conn.cursor(dictionary=True)
    # Fetch bugs for dropdown (with software name)
    cursor.execute("""
        SELECT b.Bug_ID, b.Description, b.Severity, s.Software_Name 
        FROM BUG b 
        INNER JOIN SOFTWARE s ON b.Software_ID = s.Software_ID
        ORDER BY b.Bug_ID DESC
    """)
    bugs = cursor.fetchall()

    # Fetch developers for dropdown
    cursor.execute("SELECT Developer_ID, Developer_Name, Email FROM DEVELOPER ORDER BY Developer_Name ASC")
    developers = cursor.fetchall()

    if search:
        query = """
            SELECT m.*, b.Description AS Bug_Description, dev.Developer_Name, s.Software_Name
            FROM MAINTENANCE m
            INNER JOIN BUG b ON m.Bug_ID = b.Bug_ID
            INNER JOIN SOFTWARE s ON b.Software_ID = s.Software_ID
            INNER JOIN DEVELOPER dev ON m.Performed_By = dev.Developer_ID
            WHERE m.Description LIKE %s OR dev.Developer_Name LIKE %s OR m.Status LIKE %s OR b.Description LIKE %s
            ORDER BY m.Maintenance_ID DESC
        """
        param = f"%{search}%"
        cursor.execute(query, (param, param, param, param))
    else:
        query = """
            SELECT m.*, b.Description AS Bug_Description, dev.Developer_Name, s.Software_Name
            FROM MAINTENANCE m
            INNER JOIN BUG b ON m.Bug_ID = b.Bug_ID
            INNER JOIN SOFTWARE s ON b.Software_ID = s.Software_ID
            INNER JOIN DEVELOPER dev ON m.Performed_By = dev.Developer_ID
            ORDER BY m.Maintenance_ID DESC
        """
        cursor.execute(query)
    maint_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('maintenance.html', maintenance_list=maint_list, bugs=bugs, developers=developers, search=search)


@app.route('/maintenance/add', methods=['POST'])
@login_required
def add_maintenance():
    bug_id = request.form.get('bug_id')
    maintenance_date = request.form.get('maintenance_date') or date.today().isoformat()
    description = request.form.get('description', '').strip()
    performed_by = request.form.get('performed_by')
    status = request.form.get('status', 'In Progress').strip()

    if not bug_id or not performed_by or not description:
        flash('Bug, Developer, and Description are required.', 'danger')
        return redirect(url_for('maintenance'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('maintenance'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO MAINTENANCE (Bug_ID, Maintenance_Date, Description, Performed_By, Status)
               VALUES (%s, %s, %s, %s, %s)""",
            (bug_id, maintenance_date, description, performed_by, status)
        )
        cursor.close()
        conn.close()
        flash('Maintenance record logged successfully.', 'success')
    except Error as e:
        flash(f'Error logging maintenance: {e}', 'danger')

    return redirect(url_for('maintenance'))


@app.route('/maintenance/edit/<int:id>', methods=['POST'])
@login_required
def edit_maintenance(id):
    bug_id = request.form.get('bug_id')
    maintenance_date = request.form.get('maintenance_date')
    description = request.form.get('description', '').strip()
    performed_by = request.form.get('performed_by')
    status = request.form.get('status', 'In Progress').strip()

    if not bug_id or not performed_by or not description or not maintenance_date:
        flash('All fields are required.', 'danger')
        return redirect(url_for('maintenance'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('maintenance'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE MAINTENANCE 
               SET Bug_ID = %s, Maintenance_Date = %s, Description = %s, Performed_By = %s, Status = %s 
               WHERE Maintenance_ID = %s""",
            (bug_id, maintenance_date, description, performed_by, status, id)
        )
        cursor.close()
        conn.close()
        flash('Maintenance record updated successfully.', 'success')
    except Error as e:
        flash(f'Error updating maintenance: {e}', 'danger')

    return redirect(url_for('maintenance'))


@app.route('/maintenance/delete/<int:id>', methods=['POST'])
@login_required
def delete_maintenance(id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('maintenance'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM MAINTENANCE WHERE Maintenance_ID = %s", (id,))
        cursor.close()
        conn.close()
        flash('Maintenance record deleted successfully.', 'success')
    except Error as e:
        flash(f'Error deleting maintenance: {e}', 'danger')

    return redirect(url_for('maintenance'))


# ---------------------------------------------------------------------
# LICENSE MODULE (CRUD + Search + Expiry Calculation)
# ---------------------------------------------------------------------
@app.route('/licenses')
@login_required
def licenses():
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('licenses.html', licenses=[], software_list=[], search=search, status_filter=status_filter)

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Software_ID, Software_Name FROM SOFTWARE ORDER BY Software_Name ASC")
    software_list = cursor.fetchall()

    query = """
        SELECT l.*, s.Software_Name,
               CASE 
                   WHEN l.Expiry_Date < CURDATE() THEN 'EXPIRED'
                   ELSE 'ACTIVE'
               END AS Auto_Status,
               DATEDIFF(l.Expiry_Date, CURDATE()) AS Days_Remaining
        FROM LICENSE l
        INNER JOIN SOFTWARE s ON l.Software_ID = s.Software_ID
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (l.License_Type LIKE %s OR s.Software_Name LIKE %s)"
        term = f"%{search}%"
        params.extend([term, term])
    if status_filter:
        query += " AND l.License_Status = %s"
        params.append(status_filter)

    query += " ORDER BY l.License_ID DESC"
    cursor.execute(query, tuple(params))
    license_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('licenses.html', licenses=license_list, software_list=software_list, search=search, status_filter=status_filter)


@app.route('/licenses/add', methods=['POST'])
@login_required
def add_license():
    software_id = request.form.get('software_id')
    license_type = request.form.get('license_type', '').strip()
    start_date = request.form.get('start_date')
    expiry_date = request.form.get('expiry_date')
    license_status = request.form.get('license_status', 'Active').strip()

    if not software_id or not license_type or not start_date or not expiry_date:
        flash('Software, License Type, Start Date, and Expiry Date are required.', 'danger')
        return redirect(url_for('licenses'))

    # Auto-adjust status if already expired
    if expiry_date < date.today().isoformat():
        license_status = 'Expired'

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('licenses'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO LICENSE (Software_ID, License_Type, Start_Date, Expiry_Date, License_Status)
               VALUES (%s, %s, %s, %s, %s)""",
            (software_id, license_type, start_date, expiry_date, license_status)
        )
        cursor.close()
        conn.close()
        flash('License record created successfully.', 'success')
    except Error as e:
        flash(f'Error adding license: {e}', 'danger')

    return redirect(url_for('licenses'))


@app.route('/licenses/edit/<int:id>', methods=['POST'])
@login_required
def edit_license(id):
    software_id = request.form.get('software_id')
    license_type = request.form.get('license_type', '').strip()
    start_date = request.form.get('start_date')
    expiry_date = request.form.get('expiry_date')
    license_status = request.form.get('license_status', 'Active').strip()

    if not software_id or not license_type or not start_date or not expiry_date:
        flash('All fields are required.', 'danger')
        return redirect(url_for('licenses'))

    # Auto adjust status if expiry date is past
    if expiry_date < date.today().isoformat():
        license_status = 'Expired'

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('licenses'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE LICENSE 
               SET Software_ID = %s, License_Type = %s, Start_Date = %s, Expiry_Date = %s, License_Status = %s 
               WHERE License_ID = %s""",
            (software_id, license_type, start_date, expiry_date, license_status, id)
        )
        cursor.close()
        conn.close()
        flash('License record updated successfully.', 'success')
    except Error as e:
        flash(f'Error updating license: {e}', 'danger')

    return redirect(url_for('licenses'))


@app.route('/licenses/delete/<int:id>', methods=['POST'])
@login_required
def delete_license(id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('licenses'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM LICENSE WHERE License_ID = %s", (id,))
        cursor.close()
        conn.close()
        flash('License deleted successfully.', 'success')
    except Error as e:
        flash(f'Error deleting license: {e}', 'danger')

    return redirect(url_for('licenses'))


# ---------------------------------------------------------------------
# TECHNOLOGY MODULE (CRUD + Search)
# ---------------------------------------------------------------------
@app.route('/technologies')
@login_required
def technologies():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('technologies.html', technologies=[], search=search)

    cursor = conn.cursor(dictionary=True)
    if search:
        query = """
            SELECT * FROM TECHNOLOGY 
            WHERE Technology_Name LIKE %s OR Technology_Type LIKE %s OR Version LIKE %s
            ORDER BY Technology_ID DESC
        """
        param = f"%{search}%"
        cursor.execute(query, (param, param, param))
    else:
        cursor.execute("SELECT * FROM TECHNOLOGY ORDER BY Technology_ID DESC")
    tech_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('technologies.html', technologies=tech_list, search=search)


@app.route('/technologies/add', methods=['POST'])
@login_required
def add_technology():
    name = request.form.get('technology_name', '').strip()
    tech_type = request.form.get('technology_type', '').strip()
    version = request.form.get('version', '').strip()
    description = request.form.get('description', '').strip()

    if not name or not tech_type:
        flash('Technology Name and Type are required.', 'danger')
        return redirect(url_for('technologies'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('technologies'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO TECHNOLOGY (Technology_Name, Technology_Type, Version, Description) 
               VALUES (%s, %s, %s, %s)""",
            (name, tech_type, version, description)
        )
        cursor.close()
        conn.close()
        flash(f'Technology "{name}" added successfully.', 'success')
    except Error as e:
        flash(f'Error adding technology: {e}', 'danger')

    return redirect(url_for('technologies'))


@app.route('/technologies/edit/<int:id>', methods=['POST'])
@login_required
def edit_technology(id):
    name = request.form.get('technology_name', '').strip()
    tech_type = request.form.get('technology_type', '').strip()
    version = request.form.get('version', '').strip()
    description = request.form.get('description', '').strip()

    if not name or not tech_type:
        flash('Technology Name and Type are required.', 'danger')
        return redirect(url_for('technologies'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('technologies'))

    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE TECHNOLOGY 
               SET Technology_Name = %s, Technology_Type = %s, Version = %s, Description = %s 
               WHERE Technology_ID = %s""",
            (name, tech_type, version, description, id)
        )
        cursor.close()
        conn.close()
        flash('Technology updated successfully.', 'success')
    except Error as e:
        flash(f'Error updating technology: {e}', 'danger')

    return redirect(url_for('technologies'))


@app.route('/technologies/delete/<int:id>', methods=['POST'])
@login_required
def delete_technology(id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('technologies'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM TECHNOLOGY WHERE Technology_ID = %s", (id,))
        cursor.close()
        conn.close()
        flash('Technology removed successfully.', 'success')
    except Error as e:
        flash(f'Error deleting technology: {e}', 'danger')

    return redirect(url_for('technologies'))


# ---------------------------------------------------------------------
# SQL REPORTS MODULE (The 15 College DBMS Evaluation Reports)
# ---------------------------------------------------------------------
@app.route('/reports')
@login_required
def reports():
    report_id = request.args.get('report', '1').strip()
    min_bugs = request.args.get('min_bugs', '1').strip()
    severity_param = request.args.get('severity', '').strip()

    reports_catalog = [
        {"id": "1", "title": "1. Projects with their Departments", "desc": "INNER JOIN between PROJECT and DEPARTMENT showing organizational ownership."},
        {"id": "2", "title": "2. Developers with their Departments", "desc": "INNER JOIN between DEVELOPER and DEPARTMENT displaying team allocations."},
        {"id": "3", "title": "3. Software with their Projects", "desc": "INNER JOIN between SOFTWARE and PROJECT demonstrating project containment."},
        {"id": "4", "title": "4. Software with their Versions", "desc": "INNER JOIN between SOFTWARE and VERSION displaying release histories."},
        {"id": "5", "title": "5. Software with their Bugs", "desc": "INNER JOIN between SOFTWARE and BUG tracking software defect registries."},
        {"id": "6", "title": "6. Bugs Grouped by Severity", "desc": "GROUP BY Severity with COUNT(Bug_ID) aggregate function."},
        {"id": "7", "title": "7. Bugs Grouped by Status", "desc": "GROUP BY Status with COUNT(Bug_ID) aggregate function."},
        {"id": "8", "title": "8. Maintenance Records with Developer Names", "desc": "Multi-table JOIN across MAINTENANCE, BUG, and DEVELOPER."},
        {"id": "9", "title": "9. Software with their Licenses", "desc": "JOIN between SOFTWARE and LICENSE with conditional expiry check."},
        {"id": "10", "title": "10. Software and Technologies Used", "desc": "M:N relationship traversal through SOFTWARE_TECHNOLOGY junction table."},
        {"id": "11", "title": "11. Projects Grouped by Department", "desc": "LEFT JOIN, GROUP BY Department with COUNT(Project_ID)."},
        {"id": "12", "title": "12. Developers Grouped by Department", "desc": "LEFT JOIN, GROUP BY Department with COUNT(Developer_ID)."},
        {"id": "13", "title": "13. Expired Licenses", "desc": "Date arithmetic and comparison using WHERE Expiry_Date < CURDATE()."},
        {"id": "14", "title": "14. Open Bugs", "desc": "Filter query demonstrating status criteria WHERE Status = 'Open'."},
        {"id": "15", "title": "15. Software Having More Than N Bugs", "desc": "Aggregated query using GROUP BY, COUNT(), and the HAVING clause."}
    ]

    sql_query = ""
    report_title = ""
    columns = []
    rows = []
    params = ()

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('reports.html', reports=reports_catalog, active_report=report_id, title="Database Offline", sql_query="N/A", columns=[], rows=[], min_bugs=min_bugs)

    cursor = conn.cursor(dictionary=True)

    try:
        if report_id == '1':
            report_title = "Report 1: Projects with their Departments"
            sql_query = """SELECT p.Project_ID, p.Project_Name, p.Project_Status, p.Start_Date, p.End_Date,
       d.Department_Name, d.Location, d.Contact_Email
FROM PROJECT p
INNER JOIN DEPARTMENT d ON p.Department_ID = d.Department_ID
ORDER BY p.Project_ID ASC;"""
            cursor.execute(sql_query)

        elif report_id == '2':
            report_title = "Report 2: Developers with their Departments"
            sql_query = """SELECT dev.Developer_ID, dev.Developer_Name, dev.Email,
       d.Department_Name, d.Location
FROM DEVELOPER dev
INNER JOIN DEPARTMENT d ON dev.Department_ID = d.Department_ID
ORDER BY dev.Developer_ID ASC;"""
            cursor.execute(sql_query)

        elif report_id == '3':
            report_title = "Report 3: Software with their Projects"
            sql_query = """SELECT s.Software_ID, s.Software_Name, s.Status AS Software_Status,
       p.Project_Name, p.Project_Status
FROM SOFTWARE s
INNER JOIN PROJECT p ON s.Project_ID = p.Project_ID
ORDER BY s.Software_ID ASC;"""
            cursor.execute(sql_query)

        elif report_id == '4':
            report_title = "Report 4: Software with their Versions"
            sql_query = """SELECT s.Software_Name, v.Version_ID, v.Version_Number, v.Release_Date
FROM SOFTWARE s
INNER JOIN VERSION v ON s.Software_ID = v.Software_ID
ORDER BY s.Software_Name ASC, v.Release_Date DESC;"""
            cursor.execute(sql_query)

        elif report_id == '5':
            report_title = "Report 5: Software with their Bugs"
            sql_query = """SELECT s.Software_Name, b.Bug_ID, b.Description, b.Severity, b.Status, b.Reported_Date
FROM SOFTWARE s
INNER JOIN BUG b ON s.Software_ID = b.Software_ID
ORDER BY b.Reported_Date DESC;"""
            cursor.execute(sql_query)

        elif report_id == '6':
            report_title = "Report 6: Bugs Grouped by Severity"
            sql_query = """SELECT Severity, COUNT(Bug_ID) AS Total_Bugs
FROM BUG
GROUP BY Severity
ORDER BY Total_Bugs DESC;"""
            cursor.execute(sql_query)

        elif report_id == '7':
            report_title = "Report 7: Bugs Grouped by Status"
            sql_query = """SELECT Status, COUNT(Bug_ID) AS Total_Bugs
FROM BUG
GROUP BY Status
ORDER BY Total_Bugs DESC;"""
            cursor.execute(sql_query)

        elif report_id == '8':
            report_title = "Report 8: Maintenance Records with Developer Names"
            sql_query = """SELECT m.Maintenance_ID, b.Description AS Bug_Summary, m.Maintenance_Date,
       dev.Developer_Name, dev.Email AS Developer_Email, m.Status AS Maintenance_Status
FROM MAINTENANCE m
INNER JOIN BUG b ON m.Bug_ID = b.Bug_ID
INNER JOIN DEVELOPER dev ON m.Performed_By = dev.Developer_ID
ORDER BY m.Maintenance_Date DESC;"""
            cursor.execute(sql_query)

        elif report_id == '9':
            report_title = "Report 9: Software with their Licenses"
            sql_query = """SELECT s.Software_Name, l.License_ID, l.License_Type, l.Start_Date, l.Expiry_Date,
       l.License_Status,
       CASE 
           WHEN l.Expiry_Date < CURDATE() THEN 'EXPIRED'
           ELSE 'VALID'
       END AS Expiry_Evaluation
FROM SOFTWARE s
INNER JOIN LICENSE l ON s.Software_ID = l.Software_ID
ORDER BY l.Expiry_Date ASC;"""
            cursor.execute(sql_query)

        elif report_id == '10':
            report_title = "Report 10: Software and Technologies Used (M:N Relationship)"
            sql_query = """SELECT s.Software_ID, s.Software_Name,
       GROUP_CONCAT(t.Technology_Name ORDER BY t.Technology_Name SEPARATOR ', ') AS Technologies_Used,
       COUNT(t.Technology_ID) AS Total_Tech_Count
FROM SOFTWARE s
INNER JOIN SOFTWARE_TECHNOLOGY st ON s.Software_ID = st.Software_ID
INNER JOIN TECHNOLOGY t ON st.Technology_ID = t.Technology_ID
GROUP BY s.Software_ID, s.Software_Name
ORDER BY Total_Tech_Count DESC;"""
            cursor.execute(sql_query)

        elif report_id == '11':
            report_title = "Report 11: Projects Grouped by Department"
            sql_query = """SELECT d.Department_ID, d.Department_Name, d.Location,
       COUNT(p.Project_ID) AS Total_Projects
FROM DEPARTMENT d
LEFT JOIN PROJECT p ON d.Department_ID = p.Department_ID
GROUP BY d.Department_ID, d.Department_Name, d.Location
ORDER BY Total_Projects DESC;"""
            cursor.execute(sql_query)

        elif report_id == '12':
            report_title = "Report 12: Developers Grouped by Department"
            sql_query = """SELECT d.Department_ID, d.Department_Name,
       COUNT(dev.Developer_ID) AS Total_Developers
FROM DEPARTMENT d
LEFT JOIN DEVELOPER dev ON d.Department_ID = dev.Department_ID
GROUP BY d.Department_ID, d.Department_Name
ORDER BY Total_Developers DESC;"""
            cursor.execute(sql_query)

        elif report_id == '13':
            report_title = "Report 13: Expired Licenses"
            sql_query = """SELECT l.License_ID, s.Software_Name, l.License_Type, l.Start_Date, l.Expiry_Date,
       DATEDIFF(CURDATE(), l.Expiry_Date) AS Days_Overdue
FROM LICENSE l
INNER JOIN SOFTWARE s ON l.Software_ID = s.Software_ID
WHERE l.Expiry_Date < CURDATE()
ORDER BY Days_Overdue DESC;"""
            cursor.execute(sql_query)

        elif report_id == '14':
            report_title = "Report 14: Open Bugs"
            sql_query = """SELECT b.Bug_ID, s.Software_Name, b.Description, b.Severity, b.Reported_Date
FROM BUG b
INNER JOIN SOFTWARE s ON b.Software_ID = s.Software_ID
WHERE b.Status = 'Open'
ORDER BY CASE b.Severity
    WHEN 'Critical' THEN 1
    WHEN 'High' THEN 2
    WHEN 'Medium' THEN 3
    ELSE 4 END;"""
            cursor.execute(sql_query)

        elif report_id == '15':
            report_title = "Report 15: Software Having More Than N Bugs (HAVING Clause)"
            try:
                min_threshold = int(min_bugs)
            except ValueError:
                min_threshold = 1
            sql_query = f"""SELECT s.Software_ID, s.Software_Name, s.Status,
       COUNT(b.Bug_ID) AS Bug_Count
FROM SOFTWARE s
INNER JOIN BUG b ON s.Software_ID = b.Software_ID
GROUP BY s.Software_ID, s.Software_Name, s.Status
HAVING COUNT(b.Bug_ID) >= {min_threshold}
ORDER BY Bug_Count DESC;"""
            cursor.execute(sql_query)

        rows = cursor.fetchall()
        if rows:
            columns = list(rows[0].keys())

        cursor.close()
        conn.close()

    except Error as e:
        flash(f"Error executing report query: {e}", 'danger')

    return render_template(
        'reports.html',
        reports=reports_catalog,
        active_report=report_id,
        title=report_title,
        sql_query=sql_query,
        columns=columns,
        rows=rows,
        min_bugs=min_bugs
    )


# ---------------------------------------------------------------------
# Run Application
# ---------------------------------------------------------------------
if __name__ == '__main__':
    # Start the Flask development server on port 5000
    app.run(debug=True, host='127.0.0.1', port=5000)
