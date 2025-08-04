# app/api/routes/interview.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.text.make_question import InterviewQuestionGenerator
from app.repository.interview import InterviewSession, InterviewQuestion
from app.repository.database import SessionLocal
from app.services.user.dependencies import get_current_user
import os
from dotenv import load_dotenv

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/start-interview")
def start_interview(db: Session = Depends(get_db), user_id=Depends(get_current_user)):

    # 인터뷰 세션 생성
    session = InterviewSession(user_id=user_id)
    db.add(session)
    db.flush()  # session.id 사용 가능

    # 질문 생성기
    print("질문 생성 ")
    generator = InterviewQuestionGenerator(os.getenv("GEMINI_API_KEY"))
    parsed = generator.load_structured_from_db(db, user_id)
    q1 = generator.generate_conceptual_question(parsed)
    print("질무 생성 완료")
    print("-" * 50)
    print(q1)
    # DB 저장
    db.add(InterviewQuestion(
        session_id=session.id,
        question_order=1,
        question_text=q1["question"],
        question_type=q1["question_type"]
    ))
    db.commit()

    return {
        "session_id": session.id,
        "question": q1["question"]
    }

@router.post("/generate-question/{order}")
def generate_next_question(order: int, db: Session = Depends(get_db), user_id=Depends(get_current_user)):

    # ✅ 최신 세션 조회
    session = db.query(InterviewSession).filter(
        InterviewSession.user_id == user_id
    ).order_by(InterviewSession.started_at.desc()).first()
    if not session:
        raise HTTPException(status_code=404, detail="세션 없음")

    generator = InterviewQuestionGenerator(os.getenv("GEMINI_API_KEY"))
    parsed = generator.load_structured_from_db(db, user_id)

    # ✅ 질문 생성
    if order == 2:
        q = generator.generate_technical_question(parsed)
    elif order == 3:
        q1 = db.query(InterviewQuestion).filter_by(session_id=session.id, question_order=1).first()
        q2 = db.query(InterviewQuestion).filter_by(session_id=session.id, question_order=2).first()
        a1 = q1.answer.answer_text if q1 and q1.answer else ""
        a2 = q2.answer.answer_text if q2 and q2.answer else ""
        q = generator.generate_followup_resume_question(parsed, q1.question_text, a1, q2.question_text, a2)
    elif order == 4:
        q = generator.generate_situational_question(parsed)
    elif order == 5:
        q = generator.generate_behavioral_question(parsed)
    elif order == 6:
        q4 = db.query(InterviewQuestion).filter_by(session_id=session.id, question_order=4).first()
        q5 = db.query(InterviewQuestion).filter_by(session_id=session.id, question_order=5).first()
        a4 = q4.answer.answer_text if q4 and q4.answer else ""
        a5 = q5.answer.answer_text if q5 and q5.answer else ""
        q = generator.generate_followup_coverletter_question(parsed, q4.question_text, a4, q5.question_text, a5)
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 질문 순서")

    # ✅ DB에 질문 저장
    db.add(InterviewQuestion(
        session_id=session.id,
        question_order=order,
        question_text=q["question"],
        question_type=q["question_type"]
    ))
    db.commit()

    return {
        "session_id": session.id,
        "question": q["question"]
    }