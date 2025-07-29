import os
import json
import requests
import time

class VitoSpeechClient:
    def __init__(self, token_path: str = "vito_jwt_token.json"):
        if not os.path.exists(token_path):
            raise FileNotFoundError(f"{token_path} 파일이 존재하지 않습니다.")

        with open(token_path, "r", encoding="utf-8") as f:
            token_data = json.load(f)

        self.jwt_token = token_data.get("access_token")
        if not self.jwt_token:
            raise ValueError("JWT 토큰을 JSON에서 읽을 수 없습니다.")

        self.base_url = "https://openapi.vito.ai/v1"

    def transcribe_file(self, file_path: str) -> str:
        """
        파일을 업로드하고 전사 요청을 보낸 후, transcribe_id를 반환
        """
        config = {
            "use_diarization": True,
            "diarization": {
                "spk_count": 1
            },
            "use_itn": False,
            "use_disfluency_filter": False,
            "use_profanity_filter": False,
            "use_paragraph_splitter": True,
            "paragraph_splitter": {
                "max": 50
            }
        }

        headers = {
            'Authorization': f'Bearer {self.jwt_token}'
        }

        files = {
            'file': open(file_path, 'rb')
        }

        data = {
            'config': json.dumps(config)
        }

        response = requests.post(
            f"{self.base_url}/transcribe",
            headers=headers,
            data=data,
            files=files
        )
        response.raise_for_status()

        result = response.json()
        print("📤 전송 결과:", result)
        return result["id"]

    def get_transcription_result(self, transcribe_id: str) -> dict:
        """
        전사 결과를 ID로 조회
        """
        headers = {
            'Authorization': f'bearer {self.jwt_token}'
        }

        response = requests.get(
            f"{self.base_url}/transcribe/{transcribe_id}",
            headers=headers
        )
        response.raise_for_status()

        result = response.json()
        print("📥 전사 결과:", result)
        return result

if __name__ == "__main__":
    client = VitoSpeechClient()
    transcribe_id = client.transcribe_file(r'C:\Users\UserK\AppData\Local\Temp\tmp63ci_9kv.wav')
    # 상태가 완료될 때까지 반복해서 확인
    for i in range(10):  # 최대 10번 (약 30초)
        result = client.get_transcription_result(transcribe_id)
        status = result.get("status")

        print(f"⌛️ 현재 상태: {status}")
        if status == "completed":
            break

        time.sleep(3)

    if result.get("status") == "completed":
        print("📝 전사 결과 텍스트:", result.get("text", "텍스트 없음"))
    else:
        print("❌ 전사 완료되지 않음. 나중에 다시 시도하세요.")