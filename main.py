import os
import uuid
from datetime import date, datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
import jwt
from sqlalchemy import func
from sqlalchemy.orm import Session
from auth import ALGORITHM, SECRET_KEY, create_access_token, create_refresh_token
from database import Base, engine, get_db, sessionlocal
import models
import schemas
from security import hash_password, verify_password

oauth2_scheme = HTTPBearer()

app = FastAPI(title="Employee Attendance Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "null",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "https://varshini9009.github.io"
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-create tables and ensure standard roles and Admin exist
try:
    models.Base.metadata.create_all(bind=engine)
    db_startup = sessionlocal()
    try:
        admin_role = db_startup.query(models.Role).filter(func.lower(models.Role.Role_Name) == "admin").first()
        if not admin_role:
            admin_role = models.Role(Role_Name="Admin")
            db_startup.add(admin_role)
            db_startup.commit()
            db_startup.refresh(admin_role)

        manager_role = db_startup.query(models.Role).filter(func.lower(models.Role.Role_Name) == "manager").first()
        if not manager_role:
            db_startup.add(models.Role(Role_Name="manager"))
            db_startup.commit()

        employee_role = db_startup.query(models.Role).filter(func.lower(models.Role.Role_Name) == "employee").first()
        if not employee_role:
            db_startup.add(models.Role(Role_Name="employee"))
            db_startup.commit()

        admin_user = db_startup.query(models.User).filter(models.User.Email == "admin@gmail.com").first()
        if not admin_user:
            admin_user = models.User(
                Full_Name="System Administrator",
                Email="admin@gmail.com",
                Phone="9999999999",
                Password_hash=hash_password("Admin@12345"),
                Role_Id=admin_role.Role_Id,
                Must_Change_Password=False,
                Is_Active=True
            )
            db_startup.add(admin_user)
            db_startup.commit()
    finally:
        db_startup.close()
except Exception as e:
    print(f"Startup DB init notice: {e}")


# ---------------------------------------------------------------------------
# Auth & RBAC Dependencies
# ---------------------------------------------------------------------------

def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid access token")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid access token")
        session_id = payload.get("session_id")
        if not session_id:
            raise HTTPException(status_code=401, detail="Invalid session")
        # Reject requests if the session was explicitly revoked on logout
        revoked_session = db.query(models.RevokedToken).filter(models.RevokedToken.Session_Id == session_id).first()
        if revoked_session:
            raise HTTPException(status_code=401, detail="Session has been logged out")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid access token")

    user = db.query(models.User).filter(models.User.User_Id == user_id).first()
    if not user or not user.Is_Active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    # Enforce mandatory password reset on first login
    if user.Must_Change_Password and request.url.path != "/auth/reset-password":
        raise HTTPException(status_code=403, detail="You must reset your password before accessing the application")
    return user


def require_role(allowed_roles: list[str]):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        if not current_user.role or current_user.role.Role_Name.lower() not in allowed_roles:
            raise HTTPException(status_code=403, detail="Permission denied")
        return current_user
    return role_checker


# ---------------------------------------------------------------------------
# Authentication Routes
# ---------------------------------------------------------------------------

@app.get("/auth/me")
def get_me(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.User_Id == user.User_Id).first()
    return {
        "User_Id": user.User_Id,
        "Full_Name": user.Full_Name,
        "Email": user.Email,
        "Phone": user.Phone,
        "Role_Id": user.Role_Id,
        "Role_Name": user.role.Role_Name if user.role else "",
        "Is_Active": user.Is_Active,
        "Must_Change_Password": user.Must_Change_Password,
        "Employee_Id": employee.Employee_Id if employee else None,
        "Department": employee.Department if employee else None,
        "Designation": employee.Designation if employee else None
    }


@app.post("/auth/login")
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.Email == login_data.Email).first()
    if not user or not verify_password(login_data.Password, user.Password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.Is_Active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    session_id = uuid.uuid4().hex
    token_data = {"sub": str(user.User_Id), "session_id": session_id}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "must_change_password": user.Must_Change_Password
    }


@app.put("/auth/reset-password")
def reset_password(
    password_data: schemas.PasswordReset,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.Must_Change_Password:
        raise HTTPException(status_code=400, detail="Password reset is not required")
    if not verify_password(password_data.Temporary_Password, current_user.Password_hash):
        raise HTTPException(status_code=401, detail="Invalid temporary password")
    if password_data.New_Password == password_data.Temporary_Password:
        raise HTTPException(status_code=400, detail="New password cannot be the same as temporary password")
    current_user.Password_hash = hash_password(password_data.New_Password)
    current_user.Must_Change_Password = False
    db.commit()
    return {"message": "Password reset successfully"}


# Supports both query param and JSON body for refresh_token
@app.post("/auth/refresh")
async def refresh_access_token(request: Request, refresh_token: str = None, db: Session = Depends(get_db)):
    raw_token = refresh_token
    if not raw_token:
        try:
            body = await request.json()
            raw_token = body.get("refresh_token")
        except Exception:
            raw_token = None

    if not raw_token:
        raise HTTPException(status_code=400, detail="Refresh token required")

    try:
        payload = jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        session_id = payload.get("session_id")
        if not session_id:
            raise HTTPException(status_code=401, detail="Invalid session")
        revoked_session = db.query(models.RevokedToken).filter(models.RevokedToken.Session_Id == session_id).first()
        if revoked_session:
            raise HTTPException(status_code=401, detail="Session has been logged out. Please log in again.")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(models.User).filter(models.User.User_Id == user_id).first()
    if not user or not user.Is_Active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    new_access_token = create_access_token({"sub": str(user.User_Id), "session_id": session_id})
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


# Logout blacklists the session_id so both access and refresh tokens become invalid
@app.post("/auth/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    access_token = credentials.credentials
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid access token")
        session_id = payload.get("session_id")
        if not session_id:
            raise HTTPException(status_code=401, detail="Invalid session")
        existing_session = db.query(models.RevokedToken).filter(models.RevokedToken.Session_Id == session_id).first()
        if existing_session:
            return {"message": "Logged out successfully"}
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).replace(tzinfo=None) if exp else datetime.now(timezone.utc).replace(tzinfo=None)
        token_jti = payload.get("jti") or uuid.uuid4().hex
        revoked_session = models.RevokedToken(Token_JTI=token_jti, Session_Id=session_id, Expires_At=expires_at)
        db.add(revoked_session)
        db.commit()
        return {"message": "Logged out successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------------------------------------------------------------------------
# Manager & Employee Management (Admin)
# ---------------------------------------------------------------------------

@app.post("/Admin/managers")
@app.post("/admin/managers")
def create_manager(
    manager: schemas.managercreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    existing_user = db.query(models.User).filter(models.User.Email == manager.Email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    manager_role = db.query(models.Role).filter(func.lower(models.Role.Role_Name) == "manager").first()
    if not manager_role:
        raise HTTPException(status_code=500, detail="manager role not found")
    new_manager = models.User(
        Full_Name=manager.Full_Name,
        Email=manager.Email,
        Phone=manager.Phone,
        Password_hash=hash_password(manager.Password),
        Role_Id=manager_role.Role_Id,
        Must_Change_Password=True
    )
    db.add(new_manager)
    db.commit()
    db.refresh(new_manager)
    return {
        "message": "Manager created successfully",
        "User_Id": new_manager.User_Id,
        "Full_Name": new_manager.Full_Name,
        "Email": new_manager.Email,
        "Phone": new_manager.Phone,
        "Role_Id": new_manager.Role_Id,
        "Is_Active": new_manager.Is_Active,
        "Created_At": new_manager.Created_At
    }


# Returns active managers for employee assignment dropdowns
@app.get("/managers")
def get_managers(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    manager_role = db.query(models.Role).filter(func.lower(models.Role.Role_Name) == "manager").first()
    if not manager_role:
        raise HTTPException(status_code=404, detail="Manager role not found")
    managers = db.query(models.User).filter(models.User.Role_Id == manager_role.Role_Id, models.User.Is_Active == True).all()
    return [{"User_Id": m.User_Id, "Full_Name": m.Full_Name} for m in managers]


# Creates User account and linked Employee record atomically
@app.post("/auth/register-employee", response_model=schemas.userresponse)
def register_employee(
    employee: schemas.usercreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    employee_role = db.query(models.Role).filter(func.lower(models.Role.Role_Name) == "employee").first()
    if not employee_role:
        raise HTTPException(status_code=500, detail="Employee role not found")
    manager_role = db.query(models.Role).filter(func.lower(models.Role.Role_Name) == "manager").first()
    manager = (
        db.query(models.User).filter(models.User.User_Id == employee.Manager_Id, models.User.Role_Id == manager_role.Role_Id).first()
        if manager_role else None
    )
    if not manager:
        raise HTTPException(status_code=400, detail="Invalid Manager ID")
    if not manager.Is_Active:
        raise HTTPException(status_code=400, detail="Manager is inactive")
    if db.query(models.User).filter(models.User.Email == employee.Email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(models.Employee).filter(models.Employee.Employee_Id == employee.Employee_Id).first():
        raise HTTPException(status_code=400, detail="Employee ID already exists")

    try:
        new_user = models.User(
            Full_Name=employee.Full_Name,
            Email=employee.Email,
            Phone=employee.Phone,
            Password_hash=hash_password(employee.Password),
            Role_Id=employee_role.Role_Id,
            Must_Change_Password=True
        )
        db.add(new_user)
        db.flush()
        new_employee = models.Employee(
            Employee_Id=employee.Employee_Id,
            User_Id=new_user.User_Id,
            Manager_Id=employee.Manager_Id,
            Department=employee.Department,
            Designation=employee.Designation,
            Employee_Name=employee.Full_Name,
            Email=employee.Email,
            Phone=employee.Phone
        )
        db.add(new_employee)
        db.commit()
        db.refresh(new_user)
        db.refresh(new_employee)
        return {
            "Message": "Employee registered successfully",
            "User_Id": new_user.User_Id,
            "Full_Name": new_user.Full_Name,
            "Email": new_user.Email,
            "Phone": new_user.Phone,
            "Employee_Id": new_employee.Employee_Id,
            "Department": new_employee.Department,
            "Designation": new_employee.Designation,
            "Manager_Id": new_employee.Manager_Id,
            "Role_Id": new_user.Role_Id,
            "Is_Active": new_user.Is_Active,
            "Created_At": new_user.Created_At
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Employee registration failed: {str(e)}")


# Scoped: Admin views all, Manager views assigned team
@app.get("/employees")
def get_all_employees(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin", "manager"]))
):
    role = current_user.role.Role_Name.lower()
    if role == "admin":
        employees = db.query(models.Employee).all()
    else:
        employees = db.query(models.Employee).filter(models.Employee.Manager_Id == current_user.User_Id).all()

    result = []
    for emp in employees:
        user = db.query(models.User).filter(models.User.User_Id == emp.User_Id).first() if emp.User_Id else None
        result.append({
            "Employee_Id": emp.Employee_Id,
            "Employee_Name": emp.Employee_Name,
            "Email": emp.Email,
            "Phone": emp.Phone,
            "Department": emp.Department,
            "Designation": emp.Designation,
            "Manager_Id": emp.Manager_Id,
            "User_Id": emp.User_Id,
            "Is_Active": user.Is_Active if user else True
        })
    return result


@app.get("/employee/{employee_id}", response_model=schemas.employeeresponse)
@app.get("/employees/{employee_id}", response_model=schemas.employeeresponse)
def get_employee_by_id(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    role = current_user.role.Role_Name.lower()
    if role == "admin":
        return employee
    if role == "manager" and employee.Manager_Id == current_user.User_Id:
        return employee
    if role == "employee" and employee.User_Id == current_user.User_Id:
        return employee
    raise HTTPException(status_code=403, detail="Permission denied")


@app.put("/employees/{employee_id}", response_model=schemas.employeecreateresponse)
def update_employee(
    employee_id: int,
    employee_data: schemas.employeecreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    user = db.query(models.User).filter(models.User.User_Id == employee.User_Id).first() if employee.User_Id else None

    # Check for email collision with other accounts
    if employee_data.Email != employee.Email:
        existing_user = db.query(models.User).filter(
            models.User.Email == employee_data.Email,
            models.User.User_Id != (user.User_Id if user else -1)
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered to another user")

    employee.Employee_Name = employee_data.Employee_Name
    employee.Email = employee_data.Email
    employee.Phone = employee_data.Phone
    employee.Department = employee_data.Department
    employee.Designation = employee_data.Designation

    if user:
        user.Full_Name = employee_data.Employee_Name
        user.Email = employee_data.Email
        user.Phone = employee_data.Phone

    db.commit()
    db.refresh(employee)
    return {
        "message": "employee updated successfully",
        "Employee_Id": employee.Employee_Id,
        "Employee_Name": employee_data.Employee_Name,
        "Email": employee_data.Email,
        "Phone": employee_data.Phone,
        "Department": employee_data.Department,
        "Designation": employee_data.Designation
    }


# Soft-delete: deactivates user login without dropping history
@app.put("/employees/{employee_id}/deactivate")
def deactivate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    user = db.query(models.User).filter(models.User.User_Id == employee.User_Id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")
    if not user.Is_Active:
        raise HTTPException(status_code=400, detail="Employee is already inactive")
    user.Is_Active = False
    db.commit()
    return {"message": "Employee deactivated successfully"}


# Blocks hard delete if attendance or leave records exist to preserve audit trail
@app.delete("/employees/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    attendance = db.query(models.Attendance).filter(models.Attendance.Employee_Id == employee_id).first()
    leave = db.query(models.LeaveRequest).filter(models.LeaveRequest.Employee_Id == employee_id).first()
    if attendance or leave:
        raise HTTPException(status_code=400, detail="Cannot delete employee because attendance or leave records exist")

    # Cleanly remove linked user account if present
    if employee.User_Id:
        user = db.query(models.User).filter(models.User.User_Id == employee.User_Id).first()
        if user:
            db.delete(user)

    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted successfully"}


# ---------------------------------------------------------------------------
# Attendance Endpoints
# ---------------------------------------------------------------------------

# Managers and Admins mark daily attendance for employees
@app.post("/attendance", response_model=schemas.attendancecreateresponse)
def mark_attendance(
    attendance_data: schemas.attendancecreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["manager", "admin"]))
):
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == attendance_data.Employee_Id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.User_Id is None:
        raise HTTPException(status_code=403, detail="Employee account is not active")
    employee_user = db.query(models.User).filter(models.User.User_Id == employee.User_Id).first()
    if not employee_user or not employee_user.Is_Active:
        raise HTTPException(status_code=403, detail="Cannot mark attendance for an inactive employee")

    role = current_user.role.Role_Name.lower()
    if role == "manager" and employee.Manager_Id != current_user.User_Id:
        raise HTTPException(status_code=403, detail="You can mark attendance only for your assigned employees")
    existing_attendance = db.query(models.Attendance).filter(
        models.Attendance.Employee_Id == attendance_data.Employee_Id,
        models.Attendance.Attendance_Date == date.today()
    ).first()
    if existing_attendance:
        raise HTTPException(status_code=400, detail="Attendance already marked for this employee on this date")
    new_attendance = models.Attendance(
        Employee_Id=attendance_data.Employee_Id,
        Attendance_Date=date.today(),
        Status=attendance_data.Status
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    return {
        "message": "attendance marked successfully",
        "Attendance_Id": new_attendance.Attendance_Id,
        "Employee_Id": new_attendance.Employee_Id,
        "Attendance_Date": new_attendance.Attendance_Date,
        "Status": new_attendance.Status
    }


@app.get("/attendance")
def view_attendance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin", "manager", "employee"]))
):
    role = current_user.role.Role_Name.lower()
    query = db.query(models.Attendance).join(models.Employee, models.Attendance.Employee_Id == models.Employee.Employee_Id)
    if role == "admin":
        return query.all()
    if role == "manager":
        return query.filter(models.Employee.Manager_Id == current_user.User_Id).all()
    employee = db.query(models.Employee).filter(models.Employee.User_Id == current_user.User_Id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return query.filter(models.Attendance.Employee_Id == employee.Employee_Id).all()


@app.get("/attendance/employee/{employee_id}", response_model=list[schemas.attendanceresponse])
def view_attendance_by_id(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    role = current_user.role.Role_Name.lower() if current_user.role else ""
    if role != "admin" and not (role == "manager" and employee.Manager_Id == current_user.User_Id) and not (role == "employee" and employee.User_Id == current_user.User_Id):
        raise HTTPException(status_code=403, detail="Permission denied")
    attendance_records = db.query(models.Attendance).filter(models.Attendance.Employee_Id == employee_id).all()
    return attendance_records


@app.put("/attendance/{employee_id}")
def update_attendance(
    employee_id: int,
    attendance_data: schemas.attendancecreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["manager", "admin"]))
):
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.User_Id is None:
        raise HTTPException(status_code=403, detail="Employee account is not active")
    employee_user = db.query(models.User).filter(models.User.User_Id == employee.User_Id).first()
    if not employee_user or not employee_user.Is_Active:
        raise HTTPException(status_code=403, detail="Cannot update attendance for an inactive employee")

    role = current_user.role.Role_Name.lower()
    if role == "manager" and employee.Manager_Id != current_user.User_Id:
        raise HTTPException(status_code=403, detail="You can update attendance only for your assigned employees")
    attendance = db.query(models.Attendance).filter(
        models.Attendance.Employee_Id == employee_id,
        models.Attendance.Attendance_Date == date.today()
    ).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found for this employee on this date")
    attendance.Status = attendance_data.Status
    db.commit()
    db.refresh(attendance)
    return {
        "message": "attendance status updated successfully",
        "Attendance_Id": attendance.Attendance_Id,
        "Employee_Id": attendance.Employee_Id,
        "Attendance_Date": attendance.Attendance_Date,
        "Status": attendance.Status
    }


@app.delete("/attendance/{employee_id}/{attendance_date}")
def delete_attendance(
    employee_id: int,
    attendance_date: date,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["manager", "admin"]))
):
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.User_Id is None:
        raise HTTPException(status_code=403, detail="Employee account is not active")
    employee_user = db.query(models.User).filter(models.User.User_Id == employee.User_Id).first()
    if not employee_user or not employee_user.Is_Active:
        raise HTTPException(status_code=403, detail="Cannot delete attendance for an inactive employee")

    role = current_user.role.Role_Name.lower()
    if role == "manager" and employee.Manager_Id != current_user.User_Id:
        raise HTTPException(status_code=403, detail="You can delete attendance only for your assigned employees")
    attendance = db.query(models.Attendance).filter(
        models.Attendance.Employee_Id == employee_id,
        models.Attendance.Attendance_Date == attendance_date
    ).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found for this employee on this date")
    db.delete(attendance)
    db.commit()
    return {
        "message": "Attendance deleted successfully",
        "Employee_Id": employee_id,
        "Attendance_Date": attendance_date
    }


# ---------------------------------------------------------------------------
# Leave Management Endpoints
# ---------------------------------------------------------------------------

# Employees submit leave requests; checks date validity and ignores rejected records
@app.post("/leaves", response_model=schemas.leavecreateresponse)
def apply_leave(
    leave_data: schemas.leavecreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["employee"]))
):
    employee = db.query(models.Employee).filter(models.Employee.User_Id == current_user.User_Id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if leave_data.From_Date > leave_data.To_Date:
        raise HTTPException(status_code=400, detail="From date cannot be later than to date")

    # Only clash with active leaves (Pending or Approved), allow re-applying if previous was Rejected
    existing_leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.Employee_Id == employee.Employee_Id,
        models.LeaveRequest.From_Date <= leave_data.To_Date,
        models.LeaveRequest.To_Date >= leave_data.From_Date,
        func.lower(models.LeaveRequest.Status).in_(["pending", "approved"])
    ).first()
    if existing_leave:
        raise HTTPException(status_code=400, detail="Active leave request already exists for this employee on these dates")

    new_leave = models.LeaveRequest(
        Employee_Id=employee.Employee_Id,
        From_Date=leave_data.From_Date,
        To_Date=leave_data.To_Date,
        Leave_Type=leave_data.Leave_Type,
        Reason=leave_data.Reason,
        Status="Pending"
    )
    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    return {
        "message": "leave applied successfully",
        "Employee_Id": employee.Employee_Id,
        "Leave_Id": new_leave.Leave_Id,
        "From_Date": new_leave.From_Date,
        "To_Date": leave_data.To_Date,
        "Leave_Type": leave_data.Leave_Type,
        "Reason": leave_data.Reason,
        "Status": new_leave.Status
    }


@app.get("/leaves")
def view_leaves(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin", "manager", "employee"]))
):
    role = current_user.role.Role_Name.lower()
    query = db.query(models.LeaveRequest).join(models.Employee, models.LeaveRequest.Employee_Id == models.Employee.Employee_Id)
    if role == "admin":
        return query.all()
    if role == "manager":
        return query.filter(models.Employee.Manager_Id == current_user.User_Id).all()
    employee = db.query(models.Employee).filter(models.Employee.User_Id == current_user.User_Id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return query.filter(models.LeaveRequest.Employee_Id == employee.Employee_Id).all()


@app.get("/leaves/employee/{employee_id}", response_model=list[schemas.leaveresponse])
def get_leave_by_employee_id(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    role = current_user.role.Role_Name.lower() if current_user.role else ""
    if role == "manager" and employee.Manager_Id != current_user.User_Id:
        raise HTTPException(status_code=403, detail="You can view leave records only for your assigned employees")
    if role == "employee" and employee.User_Id != current_user.User_Id:
        raise HTTPException(status_code=403, detail="You can view only your own leave records")
    if role not in ["admin", "manager", "employee"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    leaves = db.query(models.LeaveRequest).filter(models.LeaveRequest.Employee_Id == employee_id).all()
    return leaves


# Only pending requests can be updated by the employee
@app.put("/leaves/employee/{employee_id}/{leave_id}", response_model=schemas.leavecreateresponse)
def update_leave(
    employee_id: int,
    leave_id: int,
    leave_data: schemas.leavecreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["employee"]))
):
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.User_Id != current_user.User_Id:
        raise HTTPException(status_code=403, detail="You can update only your own leave requests")
    leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.Employee_Id == employee_id,
        models.LeaveRequest.Leave_Id == leave_id
    ).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave_data.To_Date < leave_data.From_Date:
        raise HTTPException(status_code=400, detail="To date cannot be earlier than from date")
    if leave.Status != "Pending":
        raise HTTPException(status_code=400, detail="Cannot update a leave request that has already been reviewed by manager")

    # Ensure updated dates do not clash with another active request
    existing_leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.Employee_Id == employee.Employee_Id,
        models.LeaveRequest.Leave_Id != leave_id,
        models.LeaveRequest.From_Date <= leave_data.To_Date,
        models.LeaveRequest.To_Date >= leave_data.From_Date,
        func.lower(models.LeaveRequest.Status).in_(["pending", "approved"])
    ).first()
    if existing_leave:
        raise HTTPException(status_code=400, detail="Active leave request already exists for this employee on these dates")

    leave.From_Date = leave_data.From_Date
    leave.To_Date = leave_data.To_Date
    leave.Leave_Type = leave_data.Leave_Type
    leave.Reason = leave_data.Reason
    db.commit()
    db.refresh(leave)
    return {
        "message": "leave request updated successfully",
        "Leave_Id": leave.Leave_Id,
        "Employee_Id": leave.Employee_Id,
        "From_Date": leave.From_Date,
        "To_Date": leave.To_Date,
        "Leave_Type": leave.Leave_Type,
        "Reason": leave.Reason,
        "Status": leave.Status,
        "Reviewed_By": leave.Reviewed_By,
        "Reviewed_At": leave.Reviewed_At
    }


# Only pending requests can be deleted by the employee
@app.delete("/leaves/employee/{employee_id}/{leave_id}")
def delete_leave(
    employee_id: int,
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["employee"]))
):
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.User_Id != current_user.User_Id:
        raise HTTPException(status_code=403, detail="You can delete only your own leave requests")
    leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.Employee_Id == employee_id,
        models.LeaveRequest.Leave_Id == leave_id
    ).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave.Status != "Pending":
        raise HTTPException(status_code=400, detail="Cannot delete a leave request that has already been reviewed by manager")
    db.delete(leave)
    db.commit()
    return {"message": "Leave request deleted successfully"}


@app.get("/managers/leave-requests")
def get_manager_leave_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["manager", "admin"]))
):
    role = current_user.role.Role_Name.lower()
    query = (
        db.query(models.LeaveRequest)
        .join(models.Employee, models.LeaveRequest.Employee_Id == models.Employee.Employee_Id)
        .filter(models.LeaveRequest.Status == "Pending")
    )
    if role == "manager":
        query = query.filter(models.Employee.Manager_Id == current_user.User_Id)
    return query.all()


# Managers and Admins approve or reject leave requests
@app.put("/managers/leave-requests/{leave_id}/review")
def manager_leave_approval(
    leave_id: int,
    review_data: schemas.leaveReview,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["manager", "admin"]))
):
    leave = db.query(models.LeaveRequest).filter(models.LeaveRequest.Leave_Id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    employee = db.query(models.Employee).filter(models.Employee.Employee_Id == leave.Employee_Id).first()
    role = current_user.role.Role_Name.lower()
    if role == "manager":
        if not employee or employee.Manager_Id != current_user.User_Id:
            raise HTTPException(status_code=403, detail="You can approve or reject leave requests only for your assigned employees")
    if leave.Status != "Pending":
        raise HTTPException(status_code=400, detail="This leave request has already been reviewed")
    leave.Status = review_data.Status
    leave.Reviewed_By = current_user.User_Id
    leave.Reviewed_At = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(leave)
    return {
        "message": "Leave approved successfully" if leave.Status == "Approved" else "Leave rejected successfully",
        "Leave_Id": leave.Leave_Id,
        "Status": leave.Status,
        "Reviewed_By": leave.Reviewed_By,
        "Reviewed_At": leave.Reviewed_At
    }


# Mount frontend static files to serve the web UI directly from FastAPI root
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

