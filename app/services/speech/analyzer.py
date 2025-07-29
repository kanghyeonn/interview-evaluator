from typing import Dict, List

class SpeechSpeedAnalyzer:
    def __init__(self, result: Dict):
        """
        result는 ClovaSpeechClient의 response.json() 결과
        """
        self.result = result
        self.segments = result.get("segments", [])
        self.total_text = ""
        self.total_duration = 0.0

    def speech_speed_calculate(self) -> Dict:
        """
        내부 상태(self.segments)를 기반으로 말속도 분석 수행
        """
        for segment in self.segments:
            text = segment.get("text", "")
            start = float(segment.get("start", 0)) / 1000
            end = float(segment.get("end", 0)) / 1000
            duration = end - start

            self.total_text += text
            self.total_duration += duration

        if self.total_duration == 0:
            return {
                "syllables_per_min": 0.0,
                "words_per_min": 0.0,
                "total_duration_sec": 0.0,
                "total_text": ""
            }

        syllable_count = len(self.total_text.replace(" ", ""))
        word_count = len(self.total_text.strip().split())

        syllables_per_min = (syllable_count / self.total_duration) * 60
        words_per_min = (word_count / self.total_duration) * 60

        return {
            "syllables_per_min": round(syllables_per_min, 2),
            "words_per_min": round(words_per_min, 2),
            "total_duration_sec": round(self.total_duration, 2),
            "total_text": self.total_text.strip()
        }


if __name__ == "__main__":
    from app.services.stt.clovaspeech import ClovaSpeechClient

    client = ClovaSpeechClient()
    response = client.req_upload(file=r'C:\Users\ankh1\AppData\Local\Temp\tmpijbvpwdx.wav', completion="sync")
    result = response.json()

    analyzer = SpeechSpeedAnalyzer(result)
    analysis = analyzer.speech_speed_calculate()

    print("📝 전체 텍스트:", analysis["total_text"])
    print("🕒 발화 시간:", analysis["total_duration_sec"], "초")
    print("💬 음절 기준 속도:", analysis["syllables_per_min"], "음절/분")
    print("📖 단어 기준 속도:", analysis["words_per_min"], "단어/분")