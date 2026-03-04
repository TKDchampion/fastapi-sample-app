from sqlalchemy import create_engine, URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

_raw_url = os.getenv("DATABASE_URL")
if _raw_url:
    DATABASE_URL = _raw_url
    _using_unix_socket = False
else:
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        raise ValueError("ERROR: DATABASE_URL not setting, pls checking .env file！")

    _using_unix_socket = not DB_PORT
    if _using_unix_socket:
        # Cloud SQL Unix socket 連線：host 作為 query 參數傳入
        DATABASE_URL = URL.create(
            drivername="postgresql",
            username=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            query={"host": DB_HOST},
        )
    else:
        # TCP 連線
        DATABASE_URL = URL.create(
            drivername="postgresql",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=int(DB_PORT),
            database=DB_NAME,
        )

if not DATABASE_URL:
    raise ValueError("ERROR: DATABASE_URL not setting, pls checking .env file！")

# Unix socket 連線不支援 TCP keepalives 參數
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
