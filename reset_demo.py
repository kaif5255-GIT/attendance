# ========================================================
# Reset Demo Database Script
# Wipes all temporary/test data and leaves ONLY the clean Admin
# Ready for a live demonstration in front of your teacher!
# ========================================================

import os
from dotenv import load_dotenv
from sqlalchemy import text
from database import engine, sessionlocal
import models
from security import hash_password

load_dotenv()

print("Clearing test data for a fresh live demonstration...")

db = sessionlocal()

try:
    # Disable foreign keys and drop existing tables
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        conn.execute(text("DROP TABLE IF EXISTS Revoked_Tokens, revoked_tokens;"))
        conn.execute(text("DROP TABLE IF EXISTS Leave_Requests, leave_requests;"))
        conn.execute(text("DROP TABLE IF EXISTS Attendance, attendance;"))
        conn.execute(text("DROP TABLE IF EXISTS Employees, employees;"))
        conn.execute(text("DROP TABLE IF EXISTS Users, users;"))
        conn.execute(text("DROP TABLE IF EXISTS Roles, roles;"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        conn.commit()

    # Create fresh schema
    models.Base.metadata.create_all(bind=engine)

    # Seed roles
    admin_role = models.Role(Role_Name="Admin")
    manager_role = models.Role(Role_Name="manager")
    employee_role = models.Role(Role_Name="employee")
    db.add_all([admin_role, manager_role, employee_role])
    db.commit()

    # Seed default Admin
    admin_user = models.User(
        Full_Name="System Administrator",
        Email="admin@gmail.com",
        Phone="9999999999",
        Password_hash=hash_password("Admin@12345"),
        Role_Id=admin_role.Role_Id,
        Must_Change_Password=False,
        Is_Active=True
    )
    db.add(admin_user)
    db.commit()

    print("\n========================================================")
    print("SUCCESS: Database is 100% clean and ready for your teacher!")
    print("Zero dummy records exist. All data can be entered live:")
    print("Default Admin Login:")
    print("  Email:    admin@gmail.com")
    print("  Password: Admin@12345")
    print("========================================================\n")

except Exception as e:
    db.rollback()
    print(f"Error resetting database: {e}")

finally:
    db.close()

