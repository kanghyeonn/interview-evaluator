import json
import requests
import os
from dotenv import load_dotenv
from getJwtTokent import get_token

load_dotenv()


def get_transcribe_id():
    # JWT 토큰을 환경변수에서 읽기
    jwt_token = ""
    if not jwt_token:
        raise ValueError("환경변수 'YOUR_JWT_TOKEN'이 설정되지 않았습니다.")

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
    resp = requests.post(
        'https://openapi.vito.ai/v1/transcribe',
        headers={'Authorization': f'Bearer {jwt_token}'},
        data={'config': json.dumps(config)},
        files={'file': open(r'C:\Users\UserK\AppData\Local\Temp\tmp63ci_9kv.wav', 'rb')}
    )
    resp.raise_for_status()
    print(resp.json())
    return resp.json()