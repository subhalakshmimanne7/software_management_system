# SOFTWARE MANAGEMENT SYSTEM (SMS)
### College DBMS Project • 2nd Year CSE • Relational Database Management System

---

## 📌 Project Overview
The **Software Management System** is a complete, production-ready web application designed according to an exact 11-entity relational database schema. It facilitates complete lifecycle tracking of software products within academic or enterprise computing divisions—covering departmental ownership, engineering teams, project roadmaps, version releases, bug tracking, developer maintenance activities, software licensing, and technology stack mapping.

---

## 🗂️ Project Directory Structure

```text
software_management_system/
│
├── app.py                      # Flask backend controller (routes, auth, CRUD, reports)
├── db_config.py                # Database connection helper and auto-initializer
├── database.sql                # Complete MySQL DDL schema, constraints & sample data
├── requirements.txt            # Python dependencies (Flask, mysql-connector-python, Werkzeug)
├── README.md                   # Complete documentation, setup guide & DBMS report
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Master layout with responsive sidebar & flash alerts
│   ├── login.html              # User login page with demo credentials
│   ├── register.html           # User registration page
│   ├── dashboard.html          # Executive dashboard with 10 entity metrics & summaries
│   ├── users.html              # User management (CRUD + search)
│   ├── departments.html        # Department management (CRUD + search)
│   ├── projects.html           # Project management (CRUD + search + department dropdown)
│   ├── developers.html         # Developer management (CRUD + search + department dropdown)
│   ├── software.html           # Software management (CRUD + search + M:N technology stack)
│   ├── versions.html           # Version management (CRUD + search + software dropdown)
│   ├── bugs.html               # Bug management (CRUD + search + severity/status filters)
│   ├── maintenance.html        # Maintenance logs (CRUD + search + bug & developer dropdowns)
│   ├── licenses.html           # License management (CRUD + search + auto-expiry check)
│   ├── technologies.html       # Technology catalog (CRUD + search)
│   └── reports.html            # 15 Advanced SQL Evaluation Reports with live execution
│
└── static/
    ├── css/
    │   └── style.css           # Clean, responsive UI stylesheet (cards, tables, badges)
    └── js/
        └── script.js           # Modal dialogs, pre-fill edit logic, and delete confirmations
```

---

## 🧱 ER Diagram to Database Mapping

The database schema strictly implements all **11 entities** and their exact relationships without introducing any unnecessary tables:

```text
 [DEPARTMENT] 1 ───────────< N [PROJECT] (owns)
 [DEPARTMENT] 1 ───────────< N [DEVELOPER] (employs)
    [PROJECT] 1 ───────────< N [SOFTWARE] (contains)
   [SOFTWARE] 1 ───────────< N [VERSION] (has)
   [SOFTWARE] 1 ───────────< N [BUG] (has)
   [SOFTWARE] 1 ───────────< N [LICENSE] (covered_by)
   [SOFTWARE] 1 ───────────< N [SOFTWARE_TECHNOLOGY] (uses)
 [TECHNOLOGY] 1 ───────────< N [SOFTWARE_TECHNOLOGY] (used_in)
        [BUG] 1 ───────────< N [MAINTENANCE] (fixed_by)
  [DEVELOPER] 1 ───────────< N [MAINTENANCE] (performs)
       [USER] (Authentication & System Administration)
```

### Table Definitions & Primary / Foreign Keys

| Entity Table | Primary Key | Foreign Keys & References | Cardinality & Relationship |
| :--- | :--- | :--- | :--- |
| **USER** | `User_ID` | *None* (Unique on `Email`) | Independent auth entity |
| **DEPARTMENT** | `Department_ID` | *None* | 1:N with PROJECT, 1:N with DEVELOPER |
| **PROJECT** | `Project_ID` | `Department_ID` &rarr; `DEPARTMENT(Department_ID)` | N:1 with DEPARTMENT (owns) |
| **DEVELOPER** | `Developer_ID` | `Department_ID` &rarr; `DEPARTMENT(Department_ID)` | N:1 with DEPARTMENT (employs) |
| **SOFTWARE** | `Software_ID` | `Project_ID` &rarr; `PROJECT(Project_ID)` | N:1 with PROJECT (contains) |
| **VERSION** | `Version_ID` | `Software_ID` &rarr; `SOFTWARE(Software_ID)` | N:1 with SOFTWARE (has) |
| **BUG** | `Bug_ID` | `Software_ID` &rarr; `SOFTWARE(Software_ID)` | N:1 with SOFTWARE (has) |
| **MAINTENANCE** | `Maintenance_ID` | `Bug_ID` &rarr; `BUG(Bug_ID)`<br>`Performed_By` &rarr; `DEVELOPER(Developer_ID)` | N:1 with BUG (fixed_by)<br>N:1 with DEVELOPER (performs) |
| **LICENSE** | `License_ID` | `Software_ID` &rarr; `SOFTWARE(Software_ID)` | N:1 with SOFTWARE (covered_by) |
| **TECHNOLOGY** | `Technology_ID` | *None* | 1:N with SOFTWARE_TECHNOLOGY (used_in) |
| **SOFTWARE_TECHNOLOGY** | `(Software_ID, Technology_ID)` | `Software_ID` &rarr; `SOFTWARE(Software_ID)`<br>`Technology_ID` &rarr; `TECHNOLOGY(Technology_ID)` | **M:N Junction Table** between SOFTWARE & TECHNOLOGY |

---

## 🎓 DBMS Normalization Analysis

### 1. First Normal Form (1NF)
- Every column contains atomic (indivisible) values.
- No repeating groups or comma-separated lists stored in columns (technologies are properly decoupled into the `SOFTWARE_TECHNOLOGY` junction table).
- Each table has a defined Primary Key.

### 2. Second Normal Form (2NF)
- The database is in 1NF.
- Every non-key attribute is fully functionally dependent on the entire Primary Key.
- In the composite key table `SOFTWARE_TECHNOLOGY (Software_ID, Technology_ID)`, there are no partial dependencies.

### 3. Third Normal Form (3NF)
- The database is in 2NF.
- There are no transitive dependencies ($X \to Y \to Z$).
- For example, `PROJECT` only stores `Department_ID`. Department location and contact email reside solely in `DEPARTMENT`, avoiding update anomalies.
- `MAINTENANCE` references `Bug_ID` and `Performed_By` (Developer), avoiding duplication of developer or bug metadata.

---

## 🚀 Setup Instructions

### Prerequisites
1. **Python 3.8+** (Python 3.10 / 3.11 / 3.12 / 3.14)
2. **MySQL Server** (via MySQL Community Server, XAMPP, WampServer, or MariaDB)

---

### Step 1: MySQL Setup & Database Import

#### Option A: Using MySQL Command Line or MySQL Workbench
Open your terminal or MySQL command prompt and execute:

```sql
CREATE DATABASE IF NOT EXISTS software_management_system;
USE software_management_system;
SOURCE /path/to/software_management_system/database.sql;
```

*(On Windows, you can also copy-paste the contents of `database.sql` directly into MySQL Workbench or phpMyAdmin SQL tab).*

#### Option B: Using XAMPP / phpMyAdmin
1. Start **Apache** and **MySQL** in the XAMPP Control Panel.
2. Open your browser and navigate to `http://localhost/phpmyadmin`.
3. Click **Import** in the top navigation.
4. Choose the `database.sql` file from this project and click **Go**.

---

### Step 2: Configure Database Credentials (if needed)

Open `db_config.py` to inspect or adjust connection credentials:
```python
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),  # Default for XAMPP is blank ''
    'database': os.environ.get('DB_NAME', 'software_management_system'),
    'port': int(os.environ.get('DB_PORT', 3306))
}
```
*Tip: If your MySQL `root` user has a password (e.g. `root` or `admin`), set `'password': 'your_password'` or define the `DB_PASSWORD` environment variable.*

---

### Step 3: Install Python Dependencies

Open PowerShell or Command Prompt in the project directory:

```powershell
pip install -r requirements.txt
```
*(Or if using the Python launcher: `py -m pip install -r requirements.txt`)*

---

### Step 4: Run the Flask Web Server

Start the application using:

```powershell
python app.py
```
*(Or with the Python launcher: `py app.py`)*

Output in terminal:
```text
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

---

### Step 5: Open in Web Browser

Navigate to:
```text
http://127.0.0.1:5000/
```
or
```text
http://localhost:5000/
```

### Default Login Credentials:
- **Email:** `admin@sms.com`
- **Password:** `admin123`
*(You can also click "Register Account" to create a new user profile at any time).*

---

## 💻 Module-by-Module Walkthrough

1. **Dashboard (`/dashboard`)**:
   - Live entity metrics displaying counts for: Users, Departments, Projects, Developers, Software, Versions, Bugs, Maintenance, Licenses, Technologies.
   - Summary panels for: Active Projects, Active Software, Open Bugs, Expired Licenses, and Recent Maintenance logs.

2. **User Management (`/users`)**:
   - Secure user authentication and management.
   - Passwords securely hashed with `generate_password_hash` (`scrypt`/`pbkdf2`).
   - Add, View, Edit, Delete, and Search users. Prevents self-deletion of the active session account.

3. **Department Management (`/departments`)**:
   - Manage academic/corporate departments.
   - Fields: Name, Location, Contact Email, Description.
   - Foreign-key parent entity for Projects and Developers.

4. **Project Management (`/projects`)**:
   - Manage software engineering projects.
   - Foreign-key dropdown selection of owning Department (`Department_ID`).
   - Status tracking (`Planning`, `In Progress`, `Testing`, `Completed`).

5. **Developer Management (`/developers`)**:
   - Manage engineers and team leads.
   - Department assignment via dropdown.
   - Track contact emails and project affiliations.

6. **Software Management (`/software`)**:
   - Core catalog of software applications contained in projects.
   - Status indicators (`Active`, `Development`, `Testing`, `Archived`).
   - **M:N Technology Stack Integration**: Select multiple technologies from `TECHNOLOGY` using the `SOFTWARE_TECHNOLOGY` junction table. Supports interactive addition/removal of technology badges.

7. **Version Management (`/versions`)**:
   - Release tracking for applications.
   - Select software from dropdown, specify semver version numbers (e.g. `v1.2.0`), and release dates.

8. **Bug Management (`/bugs`)**:
   - Issue and defect tracker.
   - Severity tags: `Low`, `Medium`, `High`, `Critical`.
   - Status lifecycle: `Open`, `In Progress`, `Resolved`, `Closed`.
   - Multi-parameter filter search by keyword, severity, and status.

9. **Maintenance Management (`/maintenance`)**:
   - Tracks engineering fixes addressing reported bugs.
   - Foreign key dropdown for Bug reference (`Bug_ID`) and Developer performing fix (`Performed_By`).
   - Status tracking (`In Progress`, `Completed`, `Pending Review`).

10. **License Management (`/licenses`)**:
    - Software licensing agreements.
    - Automated date comparison against `CURDATE()` to dynamically flag expired licenses and count days remaining/overdue.

11. **Technology Catalog (`/technologies`)**:
    - Central repository of programming languages, libraries, databases, and frameworks.
    - Fields: Name, Category/Type, Version, Description.

12. **SQL Reports Showcase (`/reports`)**:
    - Dedicated interactive laboratory displaying all 15 required relational queries.
    - Displays raw SQL statements side-by-side with live result tables.

---

## 📊 The 15 Advanced SQL Evaluation Queries

| No. | Report Title | Relational DBMS Concepts Demonstrated |
| :--- | :--- | :--- |
| **1** | Projects with their Departments | `INNER JOIN`, Foreign Key traversal |
| **2** | Developers with their Departments | `INNER JOIN`, 1:N cardinality representation |
| **3** | Software with their Projects | `INNER JOIN`, Referential integrity |
| **4** | Software with their Versions | `INNER JOIN`, `ORDER BY` date descending |
| **5** | Software with their Bugs | Multi-table defect tracking `JOIN` |
| **6** | Bugs Grouped by Severity | `GROUP BY`, `COUNT(Bug_ID)`, Aggregate ordering |
| **7** | Bugs Grouped by Status | `GROUP BY`, `COUNT(Bug_ID)`, Pipeline status |
| **8** | Maintenance Records with Developer Names | 3-table `JOIN` (`MAINTENANCE` + `BUG` + `DEVELOPER`) |
| **9** | Software with their Licenses | `JOIN`, `CASE WHEN ... THEN` conditional expressions |
| **10** | Software & Technologies Used | M:N Junction traversal (`SOFTWARE_TECHNOLOGY`), `GROUP_CONCAT` |
| **11** | Projects Grouped by Department | `LEFT JOIN`, `GROUP BY`, Aggregate count |
| **12** | Developers Grouped by Department | `LEFT JOIN`, `GROUP BY`, Aggregate count |
| **13** | Expired Licenses | Date comparison `WHERE Expiry_Date < CURDATE()`, `DATEDIFF()` |
| **14** | Open Bugs | Filtering `WHERE Status = 'Open'`, custom severity sorting |
| **15** | Software Having More Than N Bugs | `GROUP BY`, `COUNT()`, `HAVING` clause filter threshold |

---

## 🎤 Viva & Presentation Questions Reference

**Q1: How is the Many-to-Many (M:N) relationship between SOFTWARE and TECHNOLOGY implemented?**  
*Answer:* A relational database cannot directly represent an M:N relationship without data duplication. We resolve it by introducing the junction table `SOFTWARE_TECHNOLOGY` having a composite primary key `(Software_ID, Technology_ID)` referencing both parent tables with foreign keys.

**Q2: What is the purpose of ON DELETE CASCADE?**  
*Answer:* It maintains referential integrity. When a parent record (e.g. a Project) is deleted, all dependent child records (its associated Software, Versions, and Bugs) are automatically purged, preventing orphan foreign keys.

**Q3: How do we prevent SQL Injection?**  
*Answer:* All database queries use parameterized SQL queries with `%s` placeholders (e.g. `cursor.execute("SELECT * FROM USER WHERE Email = %s", (email,))`). The MySQL connector sanitizes and escapes parameters, separating user input from SQL commands.

**Q4: How does the application identify expired licenses?**  
*Answer:* Using SQL date arithmetic with MySQL's built-in functions:
```sql
SELECT License_ID, Software_Name, Expiry_Date,
       CASE WHEN Expiry_Date < CURDATE() THEN 'EXPIRED' ELSE 'VALID' END AS Status,
       DATEDIFF(CURDATE(), Expiry_Date) AS Days_Overdue
FROM LICENSE INNER JOIN SOFTWARE ON LICENSE.Software_ID = SOFTWARE.Software_ID
WHERE Expiry_Date < CURDATE();
```
