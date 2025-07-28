# from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# router = APIRouter()

# @router.websocket("/ws/expression")
# async def websocket_expression(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             data = await websocket.receive_bytes()
#             # 여기에 MediaPipe 등으로 표정 분석 처리
#             result = "😊 웃는 중"  # 예시 결과
#             await websocket.send_json({"expression": result})
#     except WebSocketDisconnect:
#         print("🔌 표정 WebSocket 연결 종료")



from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import tempfile
import os
import cv2
import mediapipe as mp
import numpy as np

router = APIRouter()

# MediaPipe Pose 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False)
mp_drawing = mp.solutions.drawing_utils

@router.websocket("/ws/expression")
async def websocket_expression(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 1. 클라이언트로부터 WebM 데이터 수신
            data = await websocket.receive_bytes()

            # 2. 임시 WebM 파일 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as f:
                f.write(data)
                f.flush()
                webm_path = f.name

            # 3. OpenCV로 WebM 파일 읽기
            cap = cv2.VideoCapture(webm_path)
            success, frame = cap.read()

            gaze_result = "😐 시선 인식 실패"

            if success:
                # BGR → RGB 변환
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Pose 추론
                result = pose.process(image)

                if result.pose_landmarks:
                    landmarks = result.pose_landmarks.landmark

                    left_eye_x = landmarks[mp_pose.PoseLandmark.LEFT_EYE].x
                    right_eye_x = landmarks[mp_pose.PoseLandmark.RIGHT_EYE].x
                    left_ear_x = landmarks[mp_pose.PoseLandmark.LEFT_EAR].x
                    right_ear_x = landmarks[mp_pose.PoseLandmark.RIGHT_EAR].x

                    # 시선 방향 간단 추론
                    if abs(left_eye_x - left_ear_x) < abs(right_eye_x - right_ear_x):
                        gaze_result = "▶ 오른쪽을 보고 있음"
                    elif abs(right_eye_x - right_ear_x) < abs(left_eye_x - left_ear_x):
                        gaze_result = "◀ 왼쪽을 보고 있음"
                    else:
                        gaze_result = "⬆ 정면을 보고 있음"

            # 결과 전송
            await websocket.send_json({"gaze": gaze_result})
            print(gaze_result)

            # 정리
            cap.release()
            os.remove(webm_path)

    except WebSocketDisconnect:
        print("🔌 시선 WebSocket 연결 종료")