from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.repository.database import Base

class Resume(Base):
    __tablename__ = "resume"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255))
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="resumes")