from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.feedback.speechfeedback import SpeechFeedbackGenerator
from app.services.speech.speech_analyzer import SpeechAnalyzer
from app.services.stt.stt_service import STTService
import tempfile
import os
import asyncio
import subprocess
from dotenv import load_dotenv

load_dotenv()

os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin"

router = APIRouter()

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

        # result = subprocess.run(ffmpeg_cmd, capture_output=True)
        # if result.returncode != 0:
        #     print("❌ ffmpeg 변환 실패:", result.stderr.decode())
        #     await websocket.send_json({"transcript": "", "expression": "ffmpeg 변환 실패"})
        #     #os.remove(webm_path)
        #     return

        # 4. Whisper로 텍스트 추출
        # result = model.transcribe(wav_path, language='ko')
        # print("📝 STT 결과:", result["text"])

        # 4. Clova로 텍스트 추출
        # clova = ClovaSpeechClient()
        # text, data = clova.get_full_text_from_upload(wav_path, diarization=None)
        # print("📝 STT 결과:", text)
        # print(data)
        # print(wav_path)
        # stt 모델 결과 추출
        # # clova
        # clova = STTService(stt_type="clova")
        # clova_text, clova_result = clova.transcribe(wav_path)

        # # vito
        # vito = STTService(stt_type="vito")
        # vito_text, vito_result = vito.transcribe(wav_path)

        # # 분석
        # analyzer = SpeechAnalyzer(clova_result)
        # speed = analyzer.speech_speed_calculate()
        # pitch = analyzer.calculate_pitch_variation(wav_path)
        # fillers = analyzer.find_filler_words(vito_text)

        # # speech feedback 생성
        # feedback = SpeechFeedbackGenerator(speed, pitch, fillers).generate_feedback()

        # 5. 결과 전송
        await websocket.send_json({
            "transcript": "",
            "feedback": "feedback"
        })

        # os.remove(webm_path)
        # os.remove(wav_path)

    except WebSocketDisconnect:
        print("🔌 WebSocket 연결 종료")
