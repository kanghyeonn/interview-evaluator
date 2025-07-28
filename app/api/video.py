from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws/expression")
async def websocket_expression(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            # 여기에 MediaPipe 등으로 표정 분석 처리
            result = "😊 웃는 중"  # 예시 결과
            await websocket.send_json({"expression": result})
    except WebSocketDisconnect:
        print("🔌 표정 WebSocket 연결 종료")