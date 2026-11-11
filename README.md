# 🏢 Employee Attendance Management System

A clean, modern, full-stack **Employee Attendance Management System** built with minimal, standard technologies—specifically designed for college submissions, viva presentations, and live evaluations.

---

## ⚡ Super Easy 1-Click Run (Recommended)

You don't need complicated setups or database configurations to run the project.

### 🎯 Steps to Run:
1. Open the project folder in File Explorer.
2. **Double-click on `run.bat`**.
3. **That's it!** A terminal window will open, the server will start, and your web browser will automatically open:
   👉 **`http://127.0.0.1:8000`**
4. Log in with the default Admin credentials:
   - **Email:** `admin@gmail.com`
   - **Password:** `Admin@12345`

> **Note:** Keep the black terminal window open while using the application. Press `Ctrl + C` to stop.

---

## 💻 Manual Run via Terminal / CMD

If your teacher or examiner asks you to run the project manually from the Command Prompt:

### 1. Open Terminal in the Project Folder
Open CMD and navigate to your project directory:
```cmd
cd C:\Users\kaifa\Downloads\Employee-Attendance-Management--master
```
*(Or open the folder in File Explorer, click the address bar, type `cmd`, and press Enter).*

### 2. Install Requirements (First Time Only)
```cmd
pip install -r requirements.txt
```

### 3. Start the Server
```cmd
python -m uvicorn main:app --reload
```
*(If `python` is aliased, you can use `py -m uvicorn main:app --reload`).*

### 4. Open in Browser
Open Google Chrome or Microsoft Edge and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

API Interactive Documentation (Swagger UI):
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 🛠️ Minimal Technologies Used

Designed with minimal dependencies to ensure high performance and quick viva explanations:

- **Backend:** Python 3.12 (FastAPI, Uvicorn)
- **Database:** 
  - **Zero-Setup SQLite Fallback:** Automatically creates `employee_attendance.db` if MySQL is not running.
  - **MySQL Supported:** Seamlessly connects to MySQL (`employee_attendance_db`) via SQLAlchemy ORM & PyMySQL when port 3306 is active.
- **Security & Auth:** Standard JWT (`PyJWT`) + Python Standard Library `hashlib` (SHA-256 + Salt) — zero heavy external C++ hashing libraries needed.
- **Frontend:** Pure HTML5, Modern CSS3, Vanilla JavaScript (Fast, responsive, zero bulky framework overhead).

---

## 👥 Roles & Key Features

### 1. 👑 Admin Dashboard
- **Managers Hub:** View all managers as interactive cards with team counts (Total, Active, Inactive).
- **Manager Profile & Team View:** View assigned employees for any manager.
- **Manager Deletion with Reassignment:** Prevents orphan records by enforcing employee reassignment (`409 Conflict` safety).
- **Employee Directory:** View all employees with "Reports to" hierarchy details.
- **Register Employee:** Register employees with dynamic manager assignment dropdown.
- **Employee Actions:** Update profile, deactivate account, or cascade delete (attendance + leaves + user account).
- **Audit Logs:** View company-wide daily attendance and all leave records.

### 2. 👔 Manager Dashboard
- **My Team:** View assigned employees and their active status.
- **Live Attendance:** Quick-mark daily attendance (Present, Absent, Half Day, Leave).
- **History & Edit:** Update or delete today's attendance records.
- **Leave Review:** Review, approve, or reject employee leave requests with timestamps.

### 3. 👨‍💼 Employee Dashboard
- **My Profile:** View employee ID, department, designation, and reporting manager.
- **My Attendance:** View personal daily attendance history.
- **Apply for Leave:** Apply for leaves with automatic date validation and reason logging.
- **Leave Status:** Track Pending / Approved / Rejected status in real time.

---

## 🎯 Step-by-Step Viva / College Demo Flow

Follow this exact flow in front of your teacher:

1. **Clean Slate (Optional):**
   - Double-click `reset_demo.bat` to clear test data and start fresh with default Admin.
2. **Start Server:**
   - Double-click `run.bat` (browser automatically opens `http://127.0.0.1:8000`).
3. **Login as Admin:**
   - Email: `admin@gmail.com` | Password: `Admin@12345`.
4. **Create a Manager:**
   - Go to **Managers** -> **Create Manager**.
   - Enter: Full Name (`Rahul Sharma`), Email (`rahul@gmail.com`), Phone (`9876543210`), Password (`Manager@123`).
   - Click **Create manager** -> Switch to **All managers** tab to show the new manager card.
5. **Register an Employee:**
   - Go to **Employees** -> **Register**.
   - Enter: ID (`101`), Name (`Amit Kumar`), Email (`amit@gmail.com`), Phone (`9876500001`), Dept (`IT`), Desig (`Developer`).
   - Select Manager: Choose `Rahul Sharma` from the dropdown.
   - Click **Register employee**.
6. **Show Reporting Hierarchy:**
   - Go to **All employees** -> Show Amit Kumar with `"Reports to: Rahul Sharma"`.
   - Go to **Managers** -> Click Rahul Sharma's card -> Show Amit Kumar in Rahul's assigned team list.
7. **Demonstrate Attendance:**
   - Go to **Attendance** to view or mark attendance records.
8. **Demonstrate Safety (Manager Delete):**
   - Try to delete a manager who has employees -> Show that the system safely blocks deletion and prompts for employee reassignment.

---

## 🗄️ Database Setup (Optional - MySQL)

If you wish to use MySQL instead of the automatic SQLite database:

1. Start Apache & MySQL in **XAMPP**.
2. Open phpMyAdmin or MySQL Shell:
   ```sql
   CREATE DATABASE employee_attendance_db;
   USE employee_attendance_db;
   SOURCE employee_attendance.sql;
   ```
3. Create a `.env` file in the project root:
   ```env
   DB_USER=root
   DB_PASSWORD=
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_NAME=employee_attendance_db
   SECRET_KEY=my_secret_key_attendance_system_2026
   ```

---

## 📂 Project Structure

```text
Employee-Attendance-Management/
├── run.bat                            # 1-Click project runner
├── reset_demo.bat                     # 1-Click database demo reset
├── seed.bat                           # Seeds default Admin role & account
├── main.py                            # FastAPI application routes & middleware
├── models.py                          # SQLAlchemy ORM database models
├── schemas.py                         # Pydantic data schemas & validators
├── database.py                        # DB connection engine (MySQL with SQLite fallback)
├── auth.py                            # JWT token generation and verification
├── security.py                        # SHA-256 + salt password hashing
├── seed_admin.py                      # Admin seeding script
├── reset_demo.py                      # Demo wipe & seed script
├── requirements.txt                   # Minimal Python package requirements
├── employee_attendance.sql            # Clean MySQL schema with zero fake data
├── frontend/
│   ├── index.html                     # Responsive single-page web app
│   ├── script.js                      # Frontend logic & API client
│   └── style.css                      # Modern responsive styling
└── README.md                          # Comprehensive project documentation
```
