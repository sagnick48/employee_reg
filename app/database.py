import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
load_dotenv()
db_type = "sql"
password = os.getenv("POSTGRES_PASSWORD")
postgres_db = os.getenv("POSTGRES_DB")

# mongo_user = os.getenv("MONGO_USER")
# mongo_password = os.getenv("MONGO_PASSWORD")
POSTGRES_URL = (
    f"postgresql://postgres:{password}"
    f"@localhost:5432/{postgres_db}"
)

sql_engine = create_engine(
    POSTGRES_URL,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sql_engine,
)

Base = declarative_base()
MONGO_URL = "mongodb://localhost:27017/"
MONGO_DB = "employee"

mongo_client = AsyncIOMotorClient(
    MONGO_URL
)

mongo_database = mongo_client[MONGO_DB]

employees_collection = mongo_database["employees"]
def set_db_type(new_db_type: str):
    global db_type

    if new_db_type not in ["sql", "nosql"]:
        raise ValueError(
            "db_type must be either 'sql' or 'nosql'"
        )

    db_type = new_db_type
def get_db_type():
    return db_type
def get_sql_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
