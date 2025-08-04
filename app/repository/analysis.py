# app/models/analysis.py
from sqlalchemy import Column, Integer, ForeignKey, Float, String, Text, TIMESTAMP
from app.repository.database import Base
from datetime import datetime, timezone

class EvaluationResult(Base):
    __tablename__ = "evaluation_result"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("interview_question.id"), nullable=False)
    similarity = Column(Float)
    intent_score = Column(Float)
    knowledge_score = Column(Float)
    final_text_score = Column(Integer)
    model_answer = Column(Text)
    strengths = Column(Text)
    improvements = Column(Text)
    final_feedback = Column(Text)
    speed_score = Column(Integer)
    filler_score = Column(Integer)
    pitch_score = Column(Integer)
    final_speech_score = Column(Integer)
    speed_label = Column(String(20))
    fluency_label = Column(String(20))
    tone_label = Column(String(20))
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))

