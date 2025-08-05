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

# ffmpeg 경로 설정 (Windows 기준)
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin"

router = APIRouter()

@router.websocket("/ws/transcript")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    user_id = await get_user_id_from_websocket(websocket)
    session_id = websocket.query_params.get("session_id")
    question_order = websocket.query_params.get("question_order")

    if not session_id or not question_order:
        await websocket.send_json({"error": "session_id와 question_order가 필요합니다."})
        return

    question = db.query(InterviewQuestion).filter_by(
        session_id=int(session_id),
        question_order=int(question_order)
    ).first()

    if not question:
        await websocket.send_json({"error": "질문을 찾을 수 없습니다."})
        return

    question_id = question.id

    try:
        # 1. WebM 수신
        data = await websocket.receive_bytes()
        print(" 전체 WebM 데이터 수신:", len(data))

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
        print(" ffmpeg 변환 명령어:", ' '.join(ffmpeg_cmd))

        result = subprocess.run(ffmpeg_cmd, capture_output=True)
        if result.returncode != 0:
            print(" ffmpeg 변환 실패:", result.stderr.decode())
            await websocket.send_json({"transcript": "", "expression": "ffmpeg 변환 실패"})
            return

        # 4. STT 추출
        clova = STTService(stt_type="clova")
        clova_text, clova_result = clova.transcribe(wav_path)

        db: Session = SessionLocal()
        #question = db.query(InterviewQuestion).order_by(InterviewQuestion.id.desc()).first()
        question = db.query(InterviewQuestion).filter_by(id=question_id).first()

        print("-" * 50)
        print(f"[DEBUG] 사용자 ID: {user_id}")
        print(f"[DEBUG] 질문 ID: {question.id}")
        print(f"[DEBUG] 질문 session_id: {question.session_id}")
        print(f"[DEBUG] 질문 내용: {question.question_text}")
        print("-" * 50)

        # 4-1. 음성이 없으면: 0점 처리
        if clova_text.strip() == "":
            answer = InterviewAnswer(
                session_id=question.session_id,
                question_id=question_id,
                user_id=user_id,
                answer_text=""
            )
            db.add(answer)
            db.commit()

            evaluation = EvaluationResult(
                user_id=user_id,
                session_id=question.session_id,
                question_id=question_id,
                similarity=0.0,
                intent_score=0.0,
                knowledge_score=0.0,
                final_text_score=0,
                model_answer="",
                strengths="답변을 인식할 수 없습니다.",
                improvements="녹음된 음성이 없거나 인식되지 않았습니다.",
                final_feedback="음성 인식이 되지 않아 평가가 불가능합니다.",
                speed_score=0,
                filler_score=0,
                pitch_score=0,
                final_speech_score=0,
                speed_label="없음",
                fluency_label="없음",
                tone_label="없음"
            )
            db.add(evaluation)
            db.commit()

            await websocket.send_json({
                "transcript": "",
                "feedback": {
                    "feedback": "음성이 인식되지 않아 피드백을 생성할 수 없습니다.",
                    "score_detail": {
                        "speed": 0,
                        "filler": 0,
                        "pitch": 0
                    },
                    "total_score_normalized": 0.0
                }
            })
            os.remove(webm_path)
            os.remove(wav_path)
            return
        else:
            # 5. 정상 분석 프로세스
            answer = InterviewAnswer(
                session_id=question.session_id,
                question_id=question_id,
                user_id=user_id,
                answer_text=clova_text
            )
            db.add(answer)
            db.commit()

            vito = STTService(stt_type="vito")
            vito_text, vito_result = vito.transcribe(wav_path)

            orchestrator = EvaluationOrchestrator()
            result = orchestrator.evaluate_answer(
                question.question_text,
                clova_text,
                question.question_type
            )
             # 6. 음성 분석
            analyzer = SpeechAnalyzer(clova_result)
            speed = analyzer.speech_speed_calculate()
            pitch = analyzer.calculate_pitch_variation(wav_path)
            fillers = analyzer.find_filler_words(vito_text)

            feedback = SpeechFeedbackGenerator(speed, pitch, fillers).generate_feedback()
            evaluation = EvaluationResult(
                user_id=user_id,
                session_id=question.session_id,
                question_id=question_id,
                similarity=result["similarity"],
                intent_score=result["intent_score"],
                knowledge_score=result["knowledge_score"],
                final_text_score=result["final_score"],
                model_answer=result["model_answer"],
                strengths="\n".join(result["feedback"]["strengths"]),
                improvements="\n".join(result["feedback"]["improvements"]),
                final_feedback=result["feedback"]["final_feedback"],
                speed_score=feedback["score_detail"]["speed"],
                filler_score=feedback["score_detail"]["filler"],
                pitch_score=feedback["score_detail"]["pitch"],
                final_speech_score=(
                    feedback["score_detail"]["speed"] +
                    feedback["score_detail"]["filler"] +
                    feedback["score_detail"]["pitch"]
                ),
                speed_label=feedback.get("labels", {}).get("speed", "없음"),
                fluency_label=feedback.get("labels", {}).get("fluency", "없음"),
                tone_label=feedback.get("labels", {}).get("tone", "없음")
            )

            db.add(evaluation)
            db.commit()

            # 8. 프론트로 전송
            await websocket.send_json({
                "transcript": clova_text,
                "feedback": feedback
            })

            os.remove(webm_path)
            os.remove(wav_path)

    except WebSocketDisconnect:
        print("🔌 WebSocket 연결 종료")

