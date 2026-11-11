import os
from dotenv import load_dotenv
from database import sessionlocal
from sqlalchemy import func
import models
from security import hash_password

# Seeds the initial Admin account and standard roles from .env credentials
load_dotenv()

admin_name = os.getenv("ADMIN_NAME", "System Administrator")
admin_email = os.getenv("ADMIN_EMAIL", "admin@gmail.com")
admin_phone = os.getenv("ADMIN_PHONE", "9999999999")
admin_password = os.getenv("ADMIN_PASSWORD", "Admin@12345")

db = sessionlocal()

try:
    # Ensure all standard roles exist
    admin_role = db.query(models.Role).filter(func.lower(models.Role.Role_Name) == "admin").first()
    if not admin_role:
        admin_role = models.Role(Role_Name="Admin")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)

    manager_role = db.query(models.Role).filter(func.lower(models.Role.Role_Name) == "manager").first()
    if not manager_role:
        manager_role = models.Role(Role_Name="manager")
        db.add(manager_role)
        db.commit()

    employee_role = db.query(models.Role).filter(func.lower(models.Role.Role_Name) == "employee").first()
    if not employee_role:
        employee_role = models.Role(Role_Name="employee")
        db.add(employee_role)
        db.commit()

    existing_admin = db.query(models.User).filter(
        (models.User.Role_Id == admin_role.Role_Id) | (models.User.Email == admin_email)
    ).first()

    if existing_admin:
        print(f"Admin account already exists: {existing_admin.Email}")
    else:
        admin = models.User(
            Full_Name=admin_name,
            Email=admin_email,
            Phone=admin_phone,
            Password_hash=hash_password(admin_password),
            Role_Id=admin_role.Role_Id,
            Must_Change_Password=False
        )
        db.add(admin)
        db.commit()
        print(f"Admin created successfully with email: {admin_email}")

except Exception as e:
    db.rollback()
    print(f"Error seeding admin: {e}")
    raise

finally:
    db.close()
