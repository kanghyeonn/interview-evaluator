from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.repository.interview import InterviewAnswer, InterviewQuestion
from app.services.feedback.speechfeedback import SpeechFeedbackGenerator
from app.services.speech.speech_analyzer import SpeechAnalyzer
from app.services.stt.stt_service import STTService
from app.utils.auth_ws import get_user_id_from_websocket
import tempfile
import os
import asyncio
import subprocess
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.repository.database import SessionLocal
from app.services.text.orchestrator import EvaluationOrchestrator
from app.repository.analysis import EvaluationResult

load_dotenv()

os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin"

router = APIRouter()

@router.websocket("/ws/transcript")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    user_id = await get_user_id_from_websocket(websocket)
    
    print(f"user_id: {user_id}")
    question_id_str = websocket.query_params.get("question_id")
    if not question_id_str or not question_id_str.isdigit():
        await websocket.send_json({"error": "question_id가 유효하지 않습니다."})
        return
    question_id = int(question_id_str)
    if not question_id_str or not question_id_str.isdigit():
        await websocket.send_json({"error": "question_id가 유효하지 않습니다."})
        return
    
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
        # result = model.transcribe(wav_path, language='ko')
        # print("📝 STT 결과:", result["text"])

        # 4. Clova로 텍스트 추출
        # clova = ClovaSpeechClient()
        # text, data = clova.get_full_text_from_upload(wav_path, diarization=None)
        # print("📝 STT 결과:", text)
        # print(data)
        # print(wav_path)

        # stt 모델 결과 추출
        # clova
        clova = STTService(stt_type="clova")
        clova_text, clova_result = clova.transcribe(wav_path)

        db: Session = SessionLocal()
        answer = InterviewAnswer(
            question_id=question_id,
            user_id=user_id,
            answer_text=clova_text
        )
        db.add(answer)
        db.commit()

        # vito
        vito = STTService(stt_type="vito")
        vito_text, vito_result = vito.transcribe(wav_path)

        # 분석
        print("답변 분석중")
        analyzer = SpeechAnalyzer(clova_result)
        speed = analyzer.speech_speed_calculate()
        pitch = analyzer.calculate_pitch_variation(wav_path)
        fillers = analyzer.find_filler_words(vito_text)

        # speech feedback 생성
        feedback = SpeechFeedbackGenerator(speed, pitch, fillers).generate_feedback()
        labels = feedback.get("labels", {})
        score_detail = feedback.get("score_detail", {})
        total_score = feedback.get("total_score", 0)

        question = db.query(InterviewQuestion).filter_by(id=question_id).first()
        orchestrator = EvaluationOrchestrator()
        result = orchestrator.evaluate_answer(
            question.question_text,
            clova_text,
            question.question_type
        )

        evaluation = EvaluationResult(
            question_id=question_id,
            similarity=result["similarity"],
            intent_score=result["intent_score"],
            knowledge_score=result["knowledge_score"],
            final_text_score=result["final_score"],
            model_answer=result["model_answer"],
            strengths="\n".join(result["feedback"]["strengths"]),
            improvements="\n".join(result["feedback"]["improvements"]),
            final_feedback=result["feedback"]["final_feedback"],

            speed_score=score_detail.get("speed"),
            filler_score=score_detail.get("filler"),
            pitch_score=score_detail.get("pitch"),
            fianl_speech_score=total_score,
            speed_label=labels.get("speed"),
            fluency_label=labels.get("fluency"),
            tone_label=labels.get("tone")
        )

        db.add(evaluation)
        db.commit()

        print(clova_text)
        print(feedback)
        # 5. 결과 전송
        await websocket.send_json({
            "transcript": clova_text,
            "feedback": feedback
        })

        os.remove(webm_path)
        os.remove(wav_path)

    except WebSocketDisconnect:
        print("🔌 WebSocket 연결 종료")
