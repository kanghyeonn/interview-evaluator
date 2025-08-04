# app/utils/auth_ws.py
from fastapi import WebSocket, status, WebSocketException
from app.core.security import decode_access_token
from jose import ExpiredSignatureError, JWTError

async def get_user_id_from_websocket(websocket: WebSocket) -> int:
    # 1. 쿠키에서 access_token 추출
    token = websocket.cookies.get("access_token")
    if not token:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Access token missing"
        )

    # 2. 토큰 디코딩
    try:
        user_id = decode_access_token(token)  # 내부적으로 exp 확인
        return user_id

    # 3. 만료된 토큰 처리
    except ExpiredSignatureError:
        raise WebSocketException(
            code=4401,  # 사용자 정의 코드 (4000~4999 범위 권장)
            reason="Token expired"
        )

    # 4. 기타 잘못된 토큰
    except JWTError:
        raise WebSocketException(
            code=4403,
            reason="Invalid token"
        )
