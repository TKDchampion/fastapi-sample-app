from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("DATABASE_URL")
if not url:
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    if DB_PORT:
        # TCP 連線（含 port）
        url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Unix socket 連線（Cloud SQL，無 port）
        url = f"postgresql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?host={DB_HOST}"

DATABASE_URL = url
if not DATABASE_URL:
    raise ValueError("ERROR:  DATABASE_URL not setting,pls checking .env file！")

# Unix socket 連線不支援 TCP keepalives 參數
_using_unix_socket = DATABASE_URL.startswith("postgresql://") and "?host=/" in DATABASE_URL
_connect_args = (
    {}
    if _using_unix_socket
    else {
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 3,
    }
)

engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    connect_args=_connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Connect DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
