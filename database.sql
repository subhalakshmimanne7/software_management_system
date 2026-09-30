-- =====================================================================
-- DATABASE: SOFTWARE MANAGEMENT SYSTEM
-- College DBMS Project - 2nd Year CSE
-- Technology: MySQL
-- =====================================================================

-- Step 1: Create Database
CREATE DATABASE IF NOT EXISTS software_management_system;
USE software_management_system;

-- Step 2: Drop existing tables in reverse order of foreign key dependencies
DROP TABLE IF EXISTS SOFTWARE_TECHNOLOGY;
DROP TABLE IF EXISTS MAINTENANCE;
DROP TABLE IF EXISTS BUG;
DROP TABLE IF EXISTS VERSION;
DROP TABLE IF EXISTS LICENSE;
DROP TABLE IF EXISTS SOFTWARE;
DROP TABLE IF EXISTS DEVELOPER;
DROP TABLE IF EXISTS PROJECT;
DROP TABLE IF EXISTS DEPARTMENT;
DROP TABLE IF EXISTS USER;
DROP TABLE IF EXISTS TECHNOLOGY;

-- =====================================================================
-- TABLE 1: USER
-- Stores user credentials for system authentication and administration
-- =====================================================================
CREATE TABLE USER (
    User_ID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Password VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- TABLE 2: DEPARTMENT
-- Represents organizational units that own projects and employ developers
-- =====================================================================
CREATE TABLE DEPARTMENT (
    Department_ID INT PRIMARY KEY AUTO_INCREMENT,
    Department_Name VARCHAR(100) NOT NULL,
    Description TEXT,
    Location VARCHAR(100),
    Contact_Email VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- TABLE 3: PROJECT
-- Projects owned by departments; each project contains software
-- Relationship: DEPARTMENT 1:N PROJECT (owns)
-- =====================================================================
CREATE TABLE PROJECT (
    Project_ID INT PRIMARY KEY AUTO_INCREMENT,
    Project_Name VARCHAR(150) NOT NULL,
    Description TEXT,
    Start_Date DATE,
    End_Date DATE,
    Project_Status VARCHAR(50) DEFAULT 'Planning',
    Department_ID INT NOT NULL,
    FOREIGN KEY (Department_ID) REFERENCES DEPARTMENT(Department_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- TABLE 4: DEVELOPER
-- Software engineers employed by departments
-- Relationship: DEPARTMENT 1:N DEVELOPER (employs)
-- =====================================================================
CREATE TABLE DEVELOPER (
    Developer_ID INT PRIMARY KEY AUTO_INCREMENT,
    Developer_Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL,
    Department_ID INT NOT NULL,
    FOREIGN KEY (Department_ID) REFERENCES DEPARTMENT(Department_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- TABLE 5: SOFTWARE
-- Software applications developed within projects
-- Relationship: PROJECT 1:N SOFTWARE (contains)
-- =====================================================================
CREATE TABLE SOFTWARE (
    Software_ID INT PRIMARY KEY AUTO_INCREMENT,
    Software_Name VARCHAR(150) NOT NULL,
    Description TEXT,
    Status VARCHAR(50) DEFAULT 'Active',
    Project_ID INT NOT NULL,
    FOREIGN KEY (Project_ID) REFERENCES PROJECT(Project_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- TABLE 6: VERSION
-- Version release history for software products
-- Relationship: SOFTWARE 1:N VERSION (has)
-- =====================================================================
CREATE TABLE VERSION (
    Version_ID INT PRIMARY KEY AUTO_INCREMENT,
    Software_ID INT NOT NULL,
    Version_Number VARCHAR(50) NOT NULL,
    Release_Date DATE NOT NULL,
    FOREIGN KEY (Software_ID) REFERENCES SOFTWARE(Software_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- TABLE 7: BUG
-- Issues and defects reported against software
-- Relationship: SOFTWARE 1:N BUG (has)
-- =====================================================================
CREATE TABLE BUG (
    Bug_ID INT PRIMARY KEY AUTO_INCREMENT,
    Software_ID INT NOT NULL,
    Description TEXT NOT NULL,
    Severity VARCHAR(30) NOT NULL DEFAULT 'Medium',
    Status VARCHAR(30) NOT NULL DEFAULT 'Open',
    Reported_Date DATE NOT NULL,
    FOREIGN KEY (Software_ID) REFERENCES SOFTWARE(Software_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- TABLE 8: MAINTENANCE
-- Maintenance activities performed by developers to resolve bugs
-- Relationships: BUG 1:N MAINTENANCE (fixed_by)
--                DEVELOPER 1:N MAINTENANCE (performs)
-- =====================================================================
CREATE TABLE MAINTENANCE (
    Maintenance_ID INT PRIMARY KEY AUTO_INCREMENT,
    Bug_ID INT NOT NULL,
    Maintenance_Date DATE NOT NULL,
    Description TEXT NOT NULL,
    Performed_By INT NOT NULL,
    Status VARCHAR(30) NOT NULL DEFAULT 'In Progress',
    FOREIGN KEY (Bug_ID) REFERENCES BUG(Bug_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (Performed_By) REFERENCES DEVELOPER(Developer_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- TABLE 9: LICENSE
-- Software licensing agreements and expiry tracking
-- Relationship: SOFTWARE 1:N LICENSE (covered_by)
-- =====================================================================
CREATE TABLE LICENSE (
    License_ID INT PRIMARY KEY AUTO_INCREMENT,
    Software_ID INT NOT NULL,
    License_Type VARCHAR(50) NOT NULL,
    Start_Date DATE NOT NULL,
    Expiry_Date DATE NOT NULL,
    License_Status VARCHAR(30) NOT NULL DEFAULT 'Active',
    FOREIGN KEY (Software_ID) REFERENCES SOFTWARE(Software_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- TABLE 10: TECHNOLOGY
-- Programming languages, frameworks, libraries, and tools
-- =====================================================================
CREATE TABLE TECHNOLOGY (
    Technology_ID INT PRIMARY KEY AUTO_INCREMENT,
    Technology_Name VARCHAR(100) NOT NULL,
    Technology_Type VARCHAR(50) NOT NULL,
    Version VARCHAR(50),
    Description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- TABLE 11: SOFTWARE_TECHNOLOGY (Junction Table for M:N)
-- Associates software with the technologies it utilizes
-- Relationships: SOFTWARE 1:N SOFTWARE_TECHNOLOGY (uses)
--                TECHNOLOGY 1:N SOFTWARE_TECHNOLOGY (used_in)
-- =====================================================================
CREATE TABLE SOFTWARE_TECHNOLOGY (
    Software_ID INT NOT NULL,
    Technology_ID INT NOT NULL,
    PRIMARY KEY (Software_ID, Technology_ID),
    FOREIGN KEY (Software_ID) REFERENCES SOFTWARE(Software_ID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (Technology_ID) REFERENCES TECHNOLOGY(Technology_ID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- SAMPLE DATA INSERTION (Realistic data with valid foreign keys)
-- Note: User passwords are stored as scrypt/pbkdf2 hashes in production.
-- The default sample password for all users below is: 'Admin@123'
-- Werkzeug hash for 'Admin@123':
-- scrypt:32768:8:1$yMv6W2Q3y... or pbkdf2:sha256:600000$xI5d5b7y$...
-- Plaintext fallback and Werkzeug-compatible hashes are provided.
-- =====================================================================

-- 1. Insert Sample Users
-- Password hash corresponds to 'admin123' generated with Werkzeug generate_password_hash('admin123')
INSERT INTO USER (Name, Email, Password) VALUES
('System Administrator', 'admin@sms.com', 'scrypt:32768:8:1$jEYU4vilnsMMruON$a8696cbd3566358aa712ad7ec8f6de05dbeff5011208ca5470f645a75466acb928d29720b64e2c0708347957b3ab4a7d173178c4e74b4912342e7b3603bb7386'),
('Prof. Rajesh Sharma', 'rajesh.sharma@sms.com', 'scrypt:32768:8:1$jEYU4vilnsMMruON$a8696cbd3566358aa712ad7ec8f6de05dbeff5011208ca5470f645a75466acb928d29720b64e2c0708347957b3ab4a7d173178c4e74b4912342e7b3603bb7386'),
('Ananya Gupta', 'ananya.gupta@sms.com', 'scrypt:32768:8:1$jEYU4vilnsMMruON$a8696cbd3566358aa712ad7ec8f6de05dbeff5011208ca5470f645a75466acb928d29720b64e2c0708347957b3ab4a7d173178c4e74b4912342e7b3603bb7386');

-- 2. Insert Sample Departments
INSERT INTO DEPARTMENT (Department_Name, Description, Location, Contact_Email) VALUES
('Computer Science & Engineering', 'Core computing, systems engineering, and software architectures.', 'Building 3, Floor 2', 'cse.dept@college.edu'),
('Information Technology', 'Enterprise information systems, networking, and cloud services.', 'Building 2, Floor 1', 'it.dept@college.edu'),
('Data Science & AI', 'Machine learning systems, analytics platforms, and predictive modeling.', 'Academic Block A, Floor 4', 'ai.dept@college.edu'),
('Software Quality Assurance', 'Testing, code auditing, security review, and reliability engineering.', 'Innovation Center, Room 102', 'qa.dept@college.edu');

-- 3. Insert Sample Projects
INSERT INTO PROJECT (Project_Name, Description, Start_Date, End_Date, Project_Status, Department_ID) VALUES
('Campus ERP Platform', 'Integrated enterprise portal for attendance, grading, and course registration.', '2025-01-10', '2025-12-20', 'In Progress', 1),
('Healthcare Management Suite', 'Clinical workflow system for hospital records and outpatient scheduling.', '2024-06-01', '2025-05-30', 'Completed', 2),
('Predictive Analytics Engine', 'AI-powered student performance predictor and recommendation engine.', '2025-03-01', '2026-02-28', 'In Progress', 3),
('Secure Exam Portal', 'Proctored online examination software with real-time anomaly detection.', '2025-02-15', '2025-11-30', 'Planning', 4),
('Library Automation System', 'RFID enabled book tracking, cataloging, and digital fine collection.', '2024-01-15', '2024-09-30', 'Completed', 1);

-- 4. Insert Sample Developers
INSERT INTO DEVELOPER (Developer_Name, Email, Department_ID) VALUES
('Rahul Verma', 'rahul.verma@college.edu', 1),
('Priya Nair', 'priya.nair@college.edu', 1),
('Arjun Mehta', 'arjun.mehta@college.edu', 2),
('Sneha Roy', 'sneha.roy@college.edu', 2),
('Vikram Patel', 'vikram.patel@college.edu', 3),
('Neha Kulkarni', 'neha.kulkarni@college.edu', 4),
('Aditya Rao', 'aditya.rao@college.edu', 1);

-- 5. Insert Sample Software
INSERT INTO SOFTWARE (Software_Name, Description, Status, Project_ID) VALUES
('Student Attendance Tracker', 'Biometric and RFID attendance tracking web application.', 'Active', 1),
('Fee Payment Gateway Service', 'Microservice handling PCI-compliant online tuition fee transactions.', 'Active', 1),
('Electronic Medical Record App', 'HIPAA compliant patient chart and diagnostic summary management.', 'Active', 2),
('ML Model Serving API', 'FastAPI microservice exposing trained student retention models.', 'Active', 3),
('Exam Lockdown Browser Utility', 'Desktop agent preventing browser tab switching during exams.', 'Testing', 4),
('OPAC Book Search Portal', 'Online Public Access Catalog interface for library visitors.', 'Archived', 5);

-- 6. Insert Sample Versions
INSERT INTO VERSION (Software_ID, Version_Number, Release_Date) VALUES
(1, 'v1.0.0', '2025-02-01'),
(1, 'v1.1.0', '2025-04-15'),
(1, 'v2.0.0', '2025-08-10'),
(2, 'v1.0.0-rc', '2025-03-01'),
(2, 'v1.0.1', '2025-05-12'),
(3, 'v3.2.0', '2024-11-20'),
(3, 'v3.3.1', '2025-01-15'),
(4, 'v0.9.0-beta', '2025-04-01'),
(5, 'v0.1.0', '2025-06-01'),
(6, 'v1.0.0', '2024-09-15');

-- 7. Insert Sample Bugs
INSERT INTO BUG (Software_ID, Description, Severity, Status, Reported_Date) VALUES
(1, 'Attendance percentage calculation rounds down prematurely for fractional classes.', 'Medium', 'Resolved', '2025-04-16'),
(1, 'Concurrent swipe submission causes duplicate attendance records during peak hours.', 'High', 'Open', '2025-05-02'),
(2, 'Payment webhook signature verification times out under high SSL payload.', 'Critical', 'In Progress', '2025-05-10'),
(2, 'Invoice PDF generation missing GST number in header summary.', 'Low', 'Closed', '2025-03-20'),
(3, 'Patient allergy badge not rendering in red on high contrast screens.', 'Low', 'Resolved', '2025-02-14'),
(3, 'Session cookie fails to invalidate immediately on remote doctor logout.', 'High', 'Open', '2025-04-28'),
(4, 'Memory leak observed in inference worker process after 10,000 requests.', 'Critical', 'Open', '2025-05-15'),
(5, 'Lockdown browser fails to intercept dual-monitor displays on macOS.', 'High', 'In Progress', '2025-06-10');

-- 8. Insert Sample Maintenance
INSERT INTO MAINTENANCE (Bug_ID, Maintenance_Date, Description, Performed_By, Status) VALUES
(1, '2025-04-18', 'Adjusted floating point division to 2 decimal places using math.ceil rounding rule.', 1, 'Completed'),
(3, '2025-05-12', 'Increased webhook timeout threshold to 15s and added retry queue via Celery.', 3, 'In Progress'),
(4, '2025-03-22', 'Updated ReportLab template to include GSTIN variable in invoice header.', 2, 'Completed'),
(5, '2025-02-16', 'Corrected CSS specificity rule and color contrast token for allergy badge.', 4, 'Completed'),
(7, '2025-05-18', 'Profiled inference pipeline with memory-profiler; patch submitted for Tensor deallocation.', 5, 'In Progress'),
(8, '2025-06-12', 'Invoked CoreGraphics display enumeration API to disable external virtual screens.', 6, 'In Progress');

-- 9. Insert Sample Licenses
INSERT INTO LICENSE (Software_ID, License_Type, Start_Date, Expiry_Date, License_Status) VALUES
(1, 'MIT License', '2024-01-01', '2028-12-31', 'Active'),
(2, 'Commercial Proprietary', '2024-06-01', '2025-05-31', 'Expired'),
(3, 'Enterprise Subscription', '2024-03-15', '2025-03-14', 'Expired'),
(3, 'Enterprise Subscription (Renewed)', '2025-03-15', '2026-03-14', 'Active'),
(4, 'Apache 2.0', '2025-01-01', '2029-12-31', 'Active'),
(5, 'Educational Campus License', '2025-01-01', '2025-12-31', 'Active'),
(6, 'GNU GPL v3', '2023-01-01', '2024-12-31', 'Expired');

-- 10. Insert Sample Technologies
INSERT INTO TECHNOLOGY (Technology_Name, Technology_Type, Version, Description) VALUES
('Python', 'Programming Language', '3.11', 'High-level programming language known for readability and rich libraries.'),
('Flask', 'Web Framework', '3.0.2', 'Lightweight WSGI web application microframework for Python.'),
('MySQL', 'Relational Database', '8.0', 'Enterprise open-source relational database management system.'),
('JavaScript', 'Frontend Language', 'ES2023', 'Client-side dynamic scripting language for web browsers.'),
('FastAPI', 'API Framework', '0.110', 'Modern, fast web framework for building APIs with Python 3.8+.'),
('React.js', 'Frontend Framework', '18.2', 'Declarative, component-based user interface library.'),
('Docker', 'DevOps / Container', '24.0', 'Platform for developing, shipping, and running containerized applications.'),
('Redis', 'In-Memory Cache', '7.2', 'In-memory key-value data store used for caching and message queuing.');

-- 11. Insert Sample SOFTWARE_TECHNOLOGY (M:N relationship)
INSERT INTO SOFTWARE_TECHNOLOGY (Software_ID, Technology_ID) VALUES
(1, 1), -- Student Attendance: Python
(1, 2), -- Student Attendance: Flask
(1, 3), -- Student Attendance: MySQL
(1, 4), -- Student Attendance: JavaScript
(2, 1), -- Fee Payment: Python
(2, 2), -- Fee Payment: Flask
(2, 3), -- Fee Payment: MySQL
(2, 8), -- Fee Payment: Redis
(3, 3), -- Electronic Medical Record: MySQL
(3, 6), -- Electronic Medical Record: React.js
(3, 7), -- Electronic Medical Record: Docker
(4, 1), -- ML Model Serving: Python
(4, 5), -- ML Model Serving: FastAPI
(4, 7), -- ML Model Serving: Docker
(5, 4), -- Exam Lockdown: JavaScript
(6, 1), -- OPAC Book Search: Python
(6, 3); -- OPAC Book Search: MySQL

-- =====================================================================
-- 15 DEMO SQL REPORT QUERIES
-- =====================================================================

-- 1. Projects with their departments
-- SELECT p.Project_ID, p.Project_Name, p.Project_Status, d.Department_Name, d.Location
-- FROM PROJECT p
-- INNER JOIN DEPARTMENT d ON p.Department_ID = d.Department_ID;

-- 2. Developers with their departments
-- SELECT dev.Developer_ID, dev.Developer_Name, dev.Email, d.Department_Name
-- FROM DEVELOPER dev
-- INNER JOIN DEPARTMENT d ON dev.Department_ID = d.Department_ID;

-- 3. Software with their projects
-- SELECT s.Software_ID, s.Software_Name, s.Status, p.Project_Name, p.Project_Status
-- FROM SOFTWARE s
-- INNER JOIN PROJECT p ON s.Project_ID = p.Project_ID;

-- 4. Software with their versions
-- SELECT s.Software_Name, v.Version_Number, v.Release_Date
-- FROM SOFTWARE s
-- INNER JOIN VERSION v ON s.Software_ID = v.Software_ID
-- ORDER BY s.Software_Name, v.Release_Date DESC;

-- 5. Software with their bugs
-- SELECT s.Software_Name, b.Bug_ID, b.Description, b.Severity, b.Status, b.Reported_Date
-- FROM SOFTWARE s
-- INNER JOIN BUG b ON s.Software_ID = b.Software_ID;

-- 6. Bugs grouped by severity
-- SELECT Severity, COUNT(Bug_ID) AS Total_Bugs
-- FROM BUG
-- GROUP BY Severity
-- ORDER BY Total_Bugs DESC;

-- 7. Bugs grouped by status
-- SELECT Status, COUNT(Bug_ID) AS Total_Bugs
-- FROM BUG
-- GROUP BY Status;

-- 8. Maintenance records with developer names
-- SELECT m.Maintenance_ID, b.Description AS Bug_Description, m.Maintenance_Date,
--        dev.Developer_Name, m.Status AS Maintenance_Status
-- FROM MAINTENANCE m
-- INNER JOIN BUG b ON m.Bug_ID = b.Bug_ID
-- INNER JOIN DEVELOPER dev ON m.Performed_By = dev.Developer_ID;

-- 9. Software with their licenses
-- SELECT s.Software_Name, l.License_Type, l.Start_Date, l.Expiry_Date, l.License_Status,
--        CASE WHEN l.Expiry_Date < CURDATE() THEN 'EXPIRED' ELSE 'VALID' END AS Expiry_Check
-- FROM SOFTWARE s
-- INNER JOIN LICENSE l ON s.Software_ID = l.Software_ID;

-- 10. Software and technologies used
-- SELECT s.Software_Name, GROUP_CONCAT(t.Technology_Name ORDER BY t.Technology_Name SEPARATOR ', ') AS Technologies_Used
-- FROM SOFTWARE s
-- INNER JOIN SOFTWARE_TECHNOLOGY st ON s.Software_ID = st.Software_ID
-- INNER JOIN TECHNOLOGY t ON st.Technology_ID = t.Technology_ID
-- GROUP BY s.Software_ID, s.Software_Name;

-- 11. Projects grouped by department
-- SELECT d.Department_Name, COUNT(p.Project_ID) AS Project_Count
-- FROM DEPARTMENT d
-- LEFT JOIN PROJECT p ON d.Department_ID = p.Department_ID
-- GROUP BY d.Department_ID, d.Department_Name;

-- 12. Developers grouped by department
-- SELECT d.Department_Name, COUNT(dev.Developer_ID) AS Developer_Count
-- FROM DEPARTMENT d
-- LEFT JOIN DEVELOPER dev ON d.Department_ID = dev.Department_ID
-- GROUP BY d.Department_ID, d.Department_Name;

-- 13. Expired licenses
-- SELECT l.License_ID, s.Software_Name, l.License_Type, l.Expiry_Date, DATEDIFF(CURDATE(), l.Expiry_Date) AS Days_Expired
-- FROM LICENSE l
-- INNER JOIN SOFTWARE s ON l.Software_ID = s.Software_ID
-- WHERE l.Expiry_Date < CURDATE();

-- 14. Open bugs
-- SELECT b.Bug_ID, s.Software_Name, b.Description, b.Severity, b.Reported_Date
-- FROM BUG b
-- INNER JOIN SOFTWARE s ON b.Software_ID = s.Software_ID
-- WHERE b.Status = 'Open';

-- 15. Software having more than a specified number of bugs (e.g. >= 1 bug)
-- SELECT s.Software_ID, s.Software_Name, COUNT(b.Bug_ID) AS Bug_Count
-- FROM SOFTWARE s
-- INNER JOIN BUG b ON s.Software_ID = b.Software_ID
-- GROUP BY s.Software_ID, s.Software_Name
-- HAVING COUNT(b.Bug_ID) >= 1
-- ORDER BY Bug_Count DESC;
