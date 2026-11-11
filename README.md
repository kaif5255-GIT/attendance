# Employee Attendance Management System

A clean, fulnimal, standard technol-stack Employee Attendance Management System built with milogies—ideal for college submissions, demonstrations, and viva.

---

## 🛠️ Minimal Technologies Used

- **Backend:** Python (FastAPI, Uvicorn)
- **Database:** MySQL (via SQLAlchemy ORM & PyMySQL)
- **Authentication:** Standard JWT (PyJWT) + Built-in Python `hashlib` (SHA-256) for password security
- **Frontend:** Pure HTML5, CSS3, Vanilla JavaScript (No heavy frameworks like React/Angular needed)

> **Why Minimal?**
> - Uses Python's standard library `hashlib` (Zero heavy C++ compilers or `pwdlib[argon2]` needed).
> - Only 6 lightweight Python packages in `requirements.txt`.
> - Works seamlessly on any computer with XAMPP / MySQL.

---

## 🚀 How to Run the Project

### Step 1: Install Dependencies
Open terminal / command prompt in this project folder and run:
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Database (MySQL)
1. Start MySQL using **XAMPP** or MySQL service.
2. Open MySQL CLI or phpMyAdmin and import the database:
   ```sql
   CREATE DATABASE employee_attendance_db;
   USE employee_attendance_db;
   SOURCE employee_attendance.sql;
   ```
3. Check your `.env` file credentials:
   ```env
   DB_USER=root
   DB_PASSWORD=
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_NAME=employee_attendance_db
   ```

### Step 3: Run the Backend Server
```bash
uvicorn main:app --reload
```
The FastAPI backend server will start at: `http://127.0.0.1:8000`
API documentation (Swagger UI): `http://127.0.0.1:8000/docs`

### Step 4: Open Frontend
Open `frontend/index.html` in your web browser (or use VS Code Live Server).

---

## 👥 User Roles & Features

### 1. Admin
- View full employee directory
- Create new Managers
- Register new Employees & assign managers
- Update employee details or deactivate accounts
- View company-wide attendance and all leave records

### 2. Manager
- View assigned team employees
- Mark daily employee attendance (Present, Absent, Half Day, Leave)
- Update or delete attendance records for assigned employees
- Review, approve, or reject employee leave requests

### 3. Employee
- View personal attendance history
- Apply for leave with date validation
- Update or delete pending leave requests
- View profile and leave status

---

## 🔑 Default Seed Admin Credentials

- **Email:** `admin@gmail.com`
- **Password:** `Admin@12345`

---

## 🎯 Step-by-Step Live Teacher Demonstration Flow

Follow this exact flow in front of your teacher:

1. **Clean Reset Before Demo:**
   - Double click `reset_demo.bat` (wipes any previous test records and leaves ONLY the clean admin account).
2. **Start Backend Server:**
   - Double click `run.bat` (FastAPI starts on port 8000).
3. **Open Frontend:**
   - Open `frontend/index.html` in browser.
4. **Login as Admin:**
   - Login using `admin@gmail.com` / `Admin@12345`.
5. **Create a Manager:**
   - Fill "Create Manager" form (e.g. Rahul Sharma, `rahul@gmail.com`).
6. **Register an Employee:**
   - Fill "Register Employee" form (e.g. ID: 101, Amit Kumar, `amit@gmail.com`).
   - Select Manager (Rahul Sharma will appear automatically in the dropdown!).
7. **Login as Manager & Mark Attendance:**
   - Logout from Admin, Login with `rahul@gmail.com`.
   - First-time login prompts password reset (great security demonstration!).
   - In Manager Dashboard, go to "Mark Attendance", enter Employee ID `101`, select `Present`, and click Submit.
8. **Login as Employee & Apply Leave:**
   - Logout from Manager, Login with `amit@gmail.com`.
   - View Attendance -> Amit sees today's "Present" status!
   - Fill "Apply for Leave" form (Dates, Medical Leave, Fever) -> Submit.
9. **Manager Approves Leave:**
   - Login back as Manager -> "Pending Leave Requests" -> Click **Approve**!
10. **Show Live Database Updates:**
    - Show teacher phpMyAdmin / MySQL CLI to confirm all data was inserted live from the web UI!


