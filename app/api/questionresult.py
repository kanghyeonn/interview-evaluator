
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.repository.database import SessionLocal
from app.repository.analysis import EvaluationResult
from app.repository.interview import InterviewQuestion, InterviewAnswer, InterviewSession
from app.services.user.dependencies import get_current_user  # ✅ 사용자 인증 함수

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/result/latest")  # ✅ 먼저 정의해야 함
def get_latest_evaluation_result(
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user)
):
    # (1) 가장 최근 세션
    latest_session = (
        db.query(InterviewSession)
        .filter_by(user_id=user_id)
        .order_by(InterviewSession.started_at.desc())
        .first()
    )
    if not latest_session:
        raise HTTPException(status_code=404, detail="세션 없음")
    print(latest_session.id)

    # (2) 가장 최근 질문
    latest_question = (
        db.query(InterviewQuestion)
        .filter_by(session_id=latest_session.id)
        .order_by(InterviewQuestion.question_order.desc())
        .first()
    )
    print(latest_question.question_order)
    if not latest_question:
        raise HTTPException(status_code=404, detail="질문 없음")

    # (3) 답변과 평가 조회
    latest_answer = db.query(InterviewAnswer) \
        .filter_by(question_id=latest_question.id) \
        .first()
    result = db.query(EvaluationResult) \
        .filter_by(question_id=latest_question.id) \
        .order_by(EvaluationResult.created_at.desc()) \
        .first()

    if not result:
        raise HTTPException(status_code=404, detail="평가 결과 없음")

    return {
        "session_id": latest_session.id,
        "question_order": result.question_order,
        "question": latest_question.question_text,
        "user_answer": latest_answer.answer_text if latest_answer else "",
        "model_answer": result.model_answer or "",
        "strengths": result.strengths.split("\n") if result.strengths else [],
        "improvements": result.improvements.split("\n") if result.improvements else [],
        "final_feedback": result.final_feedback,
        "labels": {
            "speed": result.speed_label,
            "fluency": result.fluency_label,
            "tone": result.tone_label
        }
    }
# @router.get("/result/{question_id}")
# def get_evaluation_result(
#     question_id: int,
#     db: Session = Depends(get_db),
#     user_id: int = Depends(get_current_user)  # ✅ 쿠키 기반 인증
# ):
#     print("questionresult 실행")
#     # 1. 질문 객체 조회
#     question = db.query(InterviewQuestion).filter_by(id=question_id).first()
#     if not question:
#         raise HTTPException(status_code=404, detail="질문이 존재하지 않습니다.")
#
#     # 2. 세션 → 사용자 소유 확인
#     if question.session.user_id != user_id:
#         raise HTTPException(status_code=403, detail="접근 권한 없음")
#
#     # 3. 평가 결과 조회
#     result = db.query(EvaluationResult).filter_by(question_id=question_id).first()
#     if not result:
#         raise HTTPException(status_code=404, detail="평가 결과가 없습니다.")
#
#     # 4. 답변 조회
#     latest_session = db.query(InterviewSession) \
#         .filter_by(user_id=user_id) \
#         .order_by(InterviewSession.started_at.desc()) \
#         .first()
#
#     if not latest_session:
#         return None
#
#     # 2. 해당 세션에서 마지막 질문
#     latest_question = db.query(InterviewQuestion) \
#         .filter_by(session_id=latest_session.id) \
#         .order_by(InterviewQuestion.question_order.desc()) \
#         .first()
#
#     if not latest_question:
#         return None
#
#     # 3. 해당 질문의 답변
#     latest_answer = db.query(InterviewAnswer) \
#         .filter_by(question_id=latest_question.id) \
#         .first()
#
#     return {
#         "session_id": result.session_id,
#         "question_id": result.question_id,
#         "question": question.question_text,
#         "user_answer": latest_answer.answer_text if latest_answer else "",
#         "model_answer": result.model_answer if result.model_answer else "",
#         "strengths": result.strengths.split("\n") if result.strengths else [],
#         "improvements": result.improvements.split("\n") if result.improvements else [],
#         "final_feedback": result.final_feedback,
#         "labels": {
#             "speed": result.speed_label,
#             "fluency": result.fluency_label,
#             "tone": result.tone_label
#         }
#     }



    # return {
    #     "question": "오늘 뭐했어",
    #     "user_answer": "오늘은 아침에 운동을 하고, 점심 이후에는 프로젝트 코드를 정리했습니다.",
    #     "model_answer": "오늘 하루 동안 했던 일을 시간 순서대로 정리해서 말해보세요.",
    #     "final_score": 78,
    #     "similarity": 0.84,
    #     "intent_score": 0.8,
    #     "knowledge_score": 0.75,
    #     "strengths": [
    #         "자연스러운 말투로 답변했습니다.",
    #         "핵심적인 활동을 빠짐없이 언급했습니다."
    #     ],
    #     "improvements": [
    #         "답변 구조가 약간 흐릿하게 느껴졌습니다.",
    #         "시간 순서나 세부 활동을 좀 더 명확히 표현해보세요."
    #     ],
    #     "final_feedback": "전체적으로 자연스러운 답변이었으며, 하루 일과를 설명하는 데 무리가 없었습니다. 다만, 세부 사항을 조금 더 구체적으로 표현하면 더 좋겠습니다."
    # }
