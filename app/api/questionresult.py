from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.repository.database import SessionLocal
from app.repository.analysis import EvaluationResult
from app.repository.interview import InterviewQuestion, InterviewAnswer
from app.services.user.dependencies import get_current_user  # ✅ 사용자 인증 함수

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/result/{question_id}")
def get_evaluation_result(
    question_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)  # ✅ 쿠키 기반 인증
):
    # print("questionresult 실행")
    # # 1. 질문 객체 조회
    # question = db.query(InterviewQuestion).filter_by(id=question_id).first()
    # if not question:
    #     raise HTTPException(status_code=404, detail="질문이 존재하지 않습니다.")
    #
    # # 2. 세션 → 사용자 소유 확인
    # if question.session.user_id != user_id:
    #     raise HTTPException(status_code=403, detail="접근 권한 없음")
    #
    # # 3. 평가 결과 조회
    # result = db.query(EvaluationResult).filter_by(question_id=question_id).first()
    # if not result:
    #     raise HTTPException(status_code=404, detail="평가 결과가 없습니다.")
    #
    # # 4. 답변 조회
    # answer = db.query(InterviewAnswer).filter_by(question_id=question_id).first()
    #
    # return {
    #     "question": question.question_text,
    #     "user_answer": answer.answer_text if answer else "",
    #     "model_answer": result.model_answer if result.model_answer else "",
    #     "final_score": result.final_score,
    #     "similarity": result.similarity,
    #     "intent_score": result.intent_score,
    #     "knowledge_score": result.knowledge_score,
    #     "strengths": result.strengths.split("\n") if result.strengths else [],
    #     "improvements": result.improvements.split("\n") if result.improvements else [],
    #     "final_feedback": result.final_feedback
    # }

    return {
        "question": "오늘 뭐했어",
        "user_answer": "오늘은 아침에 운동을 하고, 점심 이후에는 프로젝트 코드를 정리했습니다.",
        "model_answer": "오늘 하루 동안 했던 일을 시간 순서대로 정리해서 말해보세요.",
        "final_score": 78,
        "similarity": 0.84,
        "intent_score": 0.8,
        "knowledge_score": 0.75,
        "strengths": [
            "자연스러운 말투로 답변했습니다.",
            "핵심적인 활동을 빠짐없이 언급했습니다."
        ],
        "improvements": [
            "답변 구조가 약간 흐릿하게 느껴졌습니다.",
            "시간 순서나 세부 활동을 좀 더 명확히 표현해보세요."
        ],
        "final_feedback": "전체적으로 자연스러운 답변이었으며, 하루 일과를 설명하는 데 무리가 없었습니다. 다만, 세부 사항을 조금 더 구체적으로 표현하면 더 좋겠습니다."
    }

