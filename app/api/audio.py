from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import tempfile
import os
import whisper
import asyncio
import subprocess

os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin"

router = APIRouter()
model = whisper.load_model("medium")

@router.websocket("/ws/transcript")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        # 1. 질문 단위로 전체 WebM 수신
        data = await websocket.receive_bytes()
        print("🔔 전체 WebM 데이터 수신:", len(data))

        # 2. 임시 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
            webm_path = f.name

        await asyncio.sleep(0.1)
        wav_path = webm_path.replace(".webm", ".wav")

        # 3. ffmpeg 변환
        ffmpeg_cmd = [
            "ffmpeg", "-i", webm_path,
            "-ar", "16000", "-ac", "1", "-f", "wav",
            wav_path, "-y", "-loglevel", "error"
        ]
        print("🔧 ffmpeg 변환 명령어:", ' '.join(ffmpeg_cmd))

        result = subprocess.run(ffmpeg_cmd, capture_output=True)
        if result.returncode != 0:
            print("❌ ffmpeg 변환 실패:", result.stderr.decode())
            await websocket.send_json({"transcript": "", "expression": "ffmpeg 변환 실패"})
            #os.remove(webm_path)
            return

        # 4. Whisper로 텍스트 추출
        result = model.transcribe(wav_path, language='ko')
        print("📝 STT 결과:", result["text"])

        # 5. 결과 전송
        await websocket.send_json({
            "transcript": result["text"]
        })

        os.remove(webm_path)
        os.remove(wav_path)

    except WebSocketDisconnect:
        print("🔌 WebSocket 연결 종료")
