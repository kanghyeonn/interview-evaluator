# from fastapi import APIRouter, WebSocket
# from app.services.vision.posture_analyzer import PostureAnalyzer
# import tempfile
# import os
# import numpy as np 
# import cv2

# router = APIRouter()

# @router.websocket("/ws/expression")
# async def expression_socket(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         # 1. 영상 수신
#         data = await websocket.receive_bytes()
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as f:
#             f.write(data)
#             f.flush()
#             os.fsync(f.fileno())
#             video_path = f.name

#         # 2. 분석
#         analyzer = PostureAnalyzer()
#         result = analyzer.analyze_video(video_path)

#         # 3. 전송
#         await websocket.send_json({"expression": f"Gaze: {result['gaze']}, Head: {result['head']}, Shoulder: {result['shoulder']}"})

#         os.remove(video_path)
#     except Exception as e:
#         print("❌ 오류:", e)
#         await websocket.send_json({"expression": "분석 실패"})

# app/api/video.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.services.vision.posture_analyzer import PostureAnalyzer
from app.services.vision.emotion_analyzer import EmotionAnalyzer
from app.utils.auth_ws import get_user_id_from_websocket
from app.repository.analysis import VideoEvaluationResult
from app.repository.interview import InterviewQuestion, InterviewSession
from app.repository.database import SessionLocal
import numpy as np
import cv2

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.websocket("/ws/expression")
async def expression_socket(websocket: WebSocket):
    await websocket.accept()
    analyzer = PostureAnalyzer()
    emotion_analyzer = EmotionAnalyzer("best.pt")

    db: Session = next(get_db())

    user_id = await get_user_id_from_websocket(websocket)

    print(f"user_id: {user_id}")
    # 1. 쿼리 파라미터에서 question_order 받기
    order_str = websocket.query_params.get("question_id")
    if not order_str or not order_str.isdigit():
        await websocket.send_json({"error": "question_order가 유효하지 않습니다."})
        return
    question_order = int(order_str)

    try:
        while True:
            data = await websocket.receive_bytes()

            # 🔁 1. 바이트 → 이미지 변환
            np_arr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                await websocket.send_json({"expression": "❌ 이미지 변환 실패"})
                continue
            #print("자세분석중~~~~~")
            # 🧠 2. 자세 분석
            result = analyzer.analyze_frame(frame)

            # 감정 분석
            emotion_analyzer.analyze_frame(frame)

            # 📢 3. 상태 판단
            warnings = []

            if not result["gaze"]:
                warnings.append("시선 주의")
            if not result["head"]:
                warnings.append("고개 방향 주의")
            if not result["shoulder"]:
                warnings.append("어깨 기울기 주의")
            if not result["pitch"]:
                warnings.append("머리 방향 주의")
            if not result["hand"]:
                warnings.append("손 등장")

            expression_status = " / ".join(warnings) if warnings else "정상 자세 👌"
            print("expression_status : ", expression_status)
            # 📤 4. 결과 전송
            await websocket.send_json({
                "expression": result
            })
            #print("결과 전송 완료!")

    except WebSocketDisconnect:
        print("🔌 WebSocket 연결 종료")
        result = analyzer.get_final_score()
        emotion_summary = emotion_analyzer.get_emotion_summary()

        # 1. 가장 최근 세션 조회
        session = (
            db.query(InterviewSession)
            .filter_by(user_id=user_id)
            .order_by(InterviewSession.started_at.desc())
            .first()
        )
        if not session:
            print("❌ 세션 없음")
            return

        # 2. session_id + question_order로 InterviewQuestion 조회
        question = (
            db.query(InterviewQuestion)
            .filter_by(session_id=session.id, question_order=question_order)
            .first()
        )
        if not question:
            print("❌ 질문 없음")
            return

        question_id = question.id

        video_result = VideoEvaluationResult(
            user_id=user_id,
            session_id=session.id,
            question_id=question.id,
            question_order=question_order,
            gaze_score=result["gaze_rate_score"],
            shoulder_warning=result["shoulder_posture_warning_count"],
            hand_warning=result["hand_posture_warning_count"],
            posture_score=result["shoulder_hand_score"],
            final_video_score=result["video_score"],
            positive_rate=emotion_summary.get("긍정", 0),
            neutral_rate=emotion_summary.get("중립", 0),
            negative_rate=emotion_summary.get("부정", 0),
            tense_rate=emotion_summary.get("긴장", 0),
            emotion_best=emotion_summary.get("best"),
            emotion_score=emotion_summary.get("score")
        )
        print("video_result----------------------------결과저장")
        db.add(video_result)
        db.commit()
    except Exception as e:
        print(f"❌ 처리 중 예외 발생: {e}")
        await websocket.send_json({"expression": "분석 중 오류 발생"})

