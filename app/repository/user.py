from sqlalchemy import Column, Integer, String, Date, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.repository.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "user"
    

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    nickname = Column(String(100), nullable=False)
    birthdate = Column(Date, nullable=False)
    desired_job = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True, default=None)

    # 관계 설정 (1:N → User:Resume)
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")