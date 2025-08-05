import cv2
from ultralytics import YOLO
from collections import defaultdict

class EmotionAnalyzer:
    def __init__(self, model_path="best.pt"):
        # YOLO 감정 분류 모델 로드
        self.model = YOLO(model_path)

        # 클래스 인덱스 → 감정명 매핑
        self.class_names = ['긍정', '중립', '부정', '긴장']

        # 감정별 카운트 초기화
        self.emotion_counter = defaultdict(int)

        # 총 프레임 수
        self.total_frames = 0

    def analyze_frame(self, frame):
        """
        단일 프레임에서 감정을 예측하고 카운트에 누적
        """
        results = self.model.predict(source=frame, save=False, conf=0.5, verbose=False)
        boxes = results[0].boxes

        if boxes is not None:
            for box in boxes:
                class_id = int(box.cls[0])
                emotion = self.class_names[class_id]
                self.emotion_counter[emotion] += 1
                self.total_frames += 1

        return self.get_current_top_emotion()

    def get_current_top_emotion(self):
        """
        현재까지 가장 많이 나온 감정 반환
        """
        if not self.emotion_counter:
            return "분석중"
        return max(self.emotion_counter.items(), key=lambda x: x[1])[0]

    def get_emotion_summary(self):
        """
        감정별 비율(%)과 best 감정, 감정 점수를 포함한 딕셔너리 반환
        """
        if self.total_frames == 0:
            return {emotion: 0 for emotion in self.class_names} | {"best": "없음", "score": 0}

        # 감정 비율 계산
        rate = {
            emotion: round((count / self.total_frames) * 100)
            for emotion, count in self.emotion_counter.items()
        }

        # 비율 총합 보정
        total = sum(rate.values())
        diff = 100 - total
        if diff != 0:
            best_emotion = max(rate, key=rate.get)
            rate[best_emotion] += diff

        best = max(self.emotion_counter, key=self.emotion_counter.get)
        rate["best"] = best
        rate["score"] = self.calculate_emotion_score(rate)

        return rate

    def calculate_emotion_score(self, emotion_distribution: dict) -> int:
        """
        감정 분포(%)를 기반으로 0~100점 사이 감정 점수를 계산
        """
        weights = {
            '긍정': 1.2,
            '중립': 0.8,
            '긴장': -0.5,
            '부정': -1.0
        }

        raw_score = sum(
            emotion_distribution.get(emotion, 0) * weights.get(emotion, 0)
            for emotion in weights
        )

        return max(0, min(100, round(raw_score)))
