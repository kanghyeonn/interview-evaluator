from typing import Dict, List, Tuple

class SpeechFeedbackGenerator:
    def __init__(self, speed_result: Dict, pitch_result: Dict, filler_result: List[Tuple[str, int]]):
        self.speed_result = speed_result
        self.pitch_result = pitch_result
        self.filler_result = filler_result

    def score_speed(self, spm: float) -> int:
        """
        말속도 점수: 이상적 범위는 280~400 음절/분 (최대 40점)
        """
        if 280 <= spm <= 400:
            return 40
        elif spm < 280:
            return max(0, int(40 - ((280 - spm) * 0.5)))
        else:  # spm > 400
            return max(0, int(40 - ((spm - 400) * 0.5)))

    def score_filler(self, count: int) -> int:
        """
        간투어 점수: 0~10개는 점진적 감점, 11개 이상은 가속 감점 (최대 40점)
        """
        if count == 0:
            return 40
        elif count <= 10:
            return int(40 - count * 2)
        else:
            return max(0, int(20 - (count - 10) * 2))

    def score_pitch(self, std: float) -> int:
        """
        음조 점수 (최대 20점):
        - 이상적 변화 범위: 10~20Hz → 20점
        - 너무 낮거나 높으면 대칭적으로 감점
        """

        # 🎯 1. 이상적 변화
        if 10 <= std <= 20:
            return 20

        # 🎯 2. 단조로운 경우 (0 ~ 10 미만)
        elif std < 10:
            # 0~3Hz → 0~5점, 3~7Hz → 6~12점, 7~10Hz → 13~17점
            if std < 3:
                return int((std / 3) * 5)  # 0~5점
            elif std < 7:
                return int(6 + ((std - 3) / 4) * 6)  # 6~12점
            else:
                return int(13 + ((std - 7) / 3) * 4)  # 13~17점

        # 🎯 3. 과도한 변화 (20 초과)
        else:
            # 20~23Hz → 17~13점, 23~27Hz → 12~6점, 27 이상 → 5~0점
            if std <= 23:
                return int(17 - ((std - 20) / 3) * 4)  # 17~13점
            elif std <= 27:
                return int(12 - ((std - 23) / 4) * 6)  # 12~6점
            else:
                return max(0, int(5 - ((std - 27) / 3) * 5))  # 5~0점

    def generate_feedback(self) -> Dict:
        """
        점수 및 자연어 피드백과 정규화 종합점수(1.0 기준) 반환
        """
        feedback_parts = []

        # 1. 말속도 분석 및 피드백
        spm = self.speed_result.get("syllables_per_min", 0)
        speed_score = self.score_speed(spm)
        if speed_score == 40:
            feedback_parts.append(f"말의 속도가 적절합니다. ({spm} 음절/분)")
        elif spm < 280:
            feedback_parts.append(f"말의 속도가 다소 느립니다. ({spm} 음절/분) 조금 더 자신감 있게 말해보세요.")
        else:
            feedback_parts.append(f"말의 속도가 빠릅니다. ({spm} 음절/분) 천천히 또박또박 말해보세요.")

        # 2. 간투어 분석 및 피드백
        filler_count = len(self.filler_result)
        filler_score = self.score_filler(filler_count)
        if filler_count == 0:
            feedback_parts.append("간투어 없이 명확하게 말했습니다!")
        elif filler_count <= 10:
            feedback_parts.append(f"간투어가 {filler_count}회 사용되었습니다. 조금만 줄이면 더 매끄러워질 거예요.")
        else:
            feedback_parts.append(f"간투어가 {filler_count}회 사용되었습니다. 말하기 전에 잠시 생각하고 말해보세요.")

        # 3. 음조 분석 및 피드백
        pitch_std = self.pitch_result.get("pitch_std", 0)
        pitch_score = self.score_pitch(pitch_std)
        feedback_parts.append(self.pitch_result.get("pitch_feedback", "음조 분석 결과 없음."))

        # 4. 가중치 기반 종합 점수 (1.0 정규화)
        weighted_score = (
            speed_score + filler_score + pitch_score
        ) / 100.0  # 총점 100 기준

        return {
            "feedback": " ".join(feedback_parts),
            "score_detail": {
                "speed": speed_score,
                "filler": filler_score,
                "pitch": pitch_score
            },
            "total_score_normalized": round(weighted_score, 2)
        }
