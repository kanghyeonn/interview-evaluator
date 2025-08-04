# app/models/interview.py

from sqlalchemy import Column, Integer, ForeignKey, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime
from app.repository.database import Base

class InterviewSession(Base):
    __tablename__ = "interview_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    started_at = Column(TIMESTAMP, default=datetime.utcnow)

    questions = relationship("InterviewQuestion", back_populates="session")


class InterviewQuestion(Base):
    __tablename__ = "interview_question"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("interview_session.id"), nullable=False)
    question_order = Column(Integer, nullable=False)  # 1~6
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="questions")
    answer = relationship("InterviewAnswer", uselist=False, back_populates="question")


class InterviewAnswer(Base):
    __tablename__ = "interview_answer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("interview_question.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    answer_text = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    question = relationship("InterviewQuestion", back_populates="answer")