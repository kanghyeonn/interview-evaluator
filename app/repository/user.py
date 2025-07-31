from sqlalchemy import Column, Integer, String, Date, Text, DateTime, func
from app.repository.database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    nickname = Column(String(100), nullable=False)
    birthdate = Column(Date, nullable=False)
    desired_job = Column(String(50), nullable=False)
    resume_text = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())