# app/api/routes/result.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.repository.database import SessionLocal
from app.repository.analysis import EvaluationResult, VideoEvaluationResult
from app.repository.interview import InterviewSession, InterviewQuestion, InterviewAnswer
from app.services.user.dependencies import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/result/full/latest")
def get_full_latest_result(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    print("=== /result/full/latest ===")
    print("user_id:", user_id)

    # 1. 가장 최근 세션 가져오기
    latest_session = (
        db.query(InterviewSession)
        .filter_by(user_id=user_id)
        .order_by(InterviewSession.started_at.desc())
        .first()
    )
    if not latest_session:
        raise HTTPException(status_code=404, detail="세션 없음")

    print("latest_session:", latest_session)

    # 2. 가장 마지막 질문 가져오기
    latest_question = (
        db.query(InterviewQuestion)
        .filter_by(session_id=latest_session.id)
        .order_by(InterviewQuestion.question_order.desc())
        .first()
    )
    if not latest_question:
        raise HTTPException(status_code=404, detail="질문 없음")
    print("latest_question:", latest_question)

    # 3. 해당 질문의 답변 가져오기
    latest_answer = db.query(InterviewAnswer) \
        .filter_by(question_id=latest_question.id) \
        .first()

    # 4. 텍스트/음성 평가 결과
    text_result = (
        db.query(EvaluationResult)
        .filter_by(question_id=latest_question.id)
        .order_by(EvaluationResult.created_at.desc())
        .first()
    )
    if not text_result:
        raise HTTPException(status_code=404, detail="EvaluationResult 없음")

    # 5. 영상 평가 결과
    video_result = (
        db.query(VideoEvaluationResult)
        .filter_by(question_id=latest_question.id)
        .order_by(VideoEvaluationResult.created_at.desc())
        .first()
    )

    return {
        "session_id": latest_session.id,
        "question_order": latest_question.question_order,
        "question": latest_question.question_text,
        "user_answer": latest_answer.answer_text if latest_answer else "",
        "model_answer": text_result.model_answer or "",
        "strengths": text_result.strengths.split("\n") if text_result.strengths else [],
        "improvements": text_result.improvements.split("\n") if text_result.improvements else [],
        "final_feedback": text_result.final_feedback,
        "labels": {
            "speed": text_result.speed_label,
            "fluency": text_result.fluency_label,
            "tone": text_result.tone_label
        },
        "video": {
            "gaze_score": video_result.gaze_score if video_result else None,
            "shoulder_warning": video_result.shoulder_warning if video_result else None,
            "hand_warning": video_result.hand_warning if video_result else None,
        },
        "best_emotion": video_result.emotion_best if video_result else None
    }
