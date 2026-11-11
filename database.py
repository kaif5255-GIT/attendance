import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

user = os.getenv("DB_USER", "root")
raw_password = os.getenv("DB_PASSWORD", "")
password = quote_plus(raw_password) if raw_password else ""
host = os.getenv("DB_HOST", "127.0.0.1")
port = os.getenv("DB_PORT", "3306")
database = os.getenv("DB_NAME", "employee_attendance_db")

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    if DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
else:
    DATABASE_URL = (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        if password
        else f"mysql+pymysql://{user}@{host}:{port}/{database}"
    )

# SSL is needed for managed cloud databases, skipped for local instances
connect_args = {}
if os.getenv("DB_SSL", "false").lower() in ("true", "1", "yes"):
    connect_args["ssl"] = {}

# Try connecting to MySQL; if MySQL is not running/installed, fallback to local SQLite database
try:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    with engine.connect() as conn:
        pass
    print(f"Connected to MySQL database: {database}")
except Exception:
    print(f"MySQL not reachable on {host}:{port}. Using local SQLite database (employee_attendance.db).")
    DATABASE_URL = "sqlite:///./employee_attendance.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency to yield a DB session per request and close it after
def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()
