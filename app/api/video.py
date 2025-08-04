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
from app.services.vision.posture_analyzer import PostureAnalyzer
from app.utils.auth_ws import get_user_id_from_websocket
import numpy as np
import cv2

router = APIRouter()

@router.websocket("/ws/expression")
async def expression_socket(websocket: WebSocket):
    await websocket.accept()
    analyzer = PostureAnalyzer()

    user_id = await get_user_id_from_websocket(websocket)
    print(f"user_id: {user_id}")

    question_id_str = websocket.query_params.get("question_id")
    if not question_id_str or not question_id_str.isdigit():
        print("if문 진입")
        await websocket.send_json({"error": "question_id가 유효하지 않습니다."})
        return
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
    except Exception as e:
        print(f"❌ 처리 중 예외 발생: {e}")
        await websocket.send_json({"expression": "분석 중 오류 발생"})

