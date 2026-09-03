from sqlalchemy import Column, String
from .database import Base
class Employee(Base):
    __tablename__ = "employees"
    id = Column(String(100), primary_key=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    department = Column(String(100),nullable=False)
