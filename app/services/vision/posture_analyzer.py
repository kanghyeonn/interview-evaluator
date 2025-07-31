import cv2
import mediapipe as mp
import numpy as np
import tempfile
from typing import Dict
import time

class PostureAnalyzer:
    def __init__(self):
        # MediaPipe 구성 요소 초기화
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_pose = mp.solutions.pose
        self.face_mesh = self.mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        # 얼굴 랜드마크
        self.LEFT_EYE_OUTER = 33
        self.LEFT_IRIS_LEFT = 471
        self.LEFT_IRIS_RIGHT = 469
        self.LEFT_IRIS_TOP = 470
        self.LEFT_IRIS_BOTTOM = 472
        self.LEFT_EYE_CENTER = 468
        self.RIGHT_EYE_OUTER = 263
        self.RIGHT_IRIS_LEFT = 476
        self.RIGHT_IRIS_RIGHT = 474
        self.RIGHT_IRIS_TOP = 475
        self.RIGHT_IRIS_BOTTOM = 477
        self.RIGHT_EYE_CENTER = 473

        # 포즈 랜드마크
        self.LEFT_EAR = self.mp_pose.PoseLandmark.LEFT_EAR
        self.RIGHT_EAR = self.mp_pose.PoseLandmark.RIGHT_EAR
        self.LEFT_SHOULDER = self.mp_pose.PoseLandmark.LEFT_SHOULDER
        self.RIGHT_SHOULDER = self.mp_pose.PoseLandmark.RIGHT_SHOULDER
        self.LEFT_INDEX = self.mp_pose.PoseLandmark.LEFT_INDEX
        self.RIGHT_INDEX = self.mp_pose.PoseLandmark.RIGHT_INDEX

        # 눈꺼풀 캘리브레이션
        self.calibration_openings = []
        self.is_calibrated = False
        self.frame_idx = 0
        self.up_thresh = 0.0
        self.down_thresh = 1.0

        # 깜빡임 감지
        self.blink_threshold = 0.015
        self.blink_cooldown_frames = 5
        self.blink_cooldown_counter = 0

        # 시선 유지 시간
        self.gaze_state = None
        self.gaze_start_time = time.time()
        self.gaze_duration_dict = {"UP": 0.0, "DOWN": 0.0, "CENTER": 0.0}

        # solvePnP용 3D 모델 포인트
        self.model_points = np.array([
            (0.0, 0.0, 0.0),       # Nose tip
            (0.0, -63.6, -12.5),   # Chin
            (-43.3, 32.7, -26.0),  # Left eye corner
            (43.3, 32.7, -26.0),   # Right eye corner
            (-28.9, -28.9, -24.1), # Left mouth
            (28.9, -28.9, -24.1)   # Right mouth
        ], dtype=np.float32)

    def get_camera_matrix(self, w, h):
        focal_length = w
        center = (w / 2, h / 2)
        return np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)

    def analyze_frame(self, frame: np.ndarray) -> Dict[str, str]:
        """
        단일 프레임에서 시선, 고개 방향, 어깨 기울기를 분석합니다.
        :param frame: BGR 이미지 프레임
        :return: 분석 결과 딕셔너리
        """
        gaze_result, head_result, shoulder_result, pitch_result, hand_result = "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN"

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        # BGR -> RGB 변환
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 얼굴 및 포즈 추정
        face_result = self.face_mesh.process(rgb)
        pose_result = self.pose.process(rgb)

        if face_result.multi_face_landmarks:
            lm = face_result.multi_face_landmarks[0].landmark

            # 좌우 시선 분석 (비율 기반)
            left_eye_outer = np.array([lm[self.LEFT_EYE_OUTER].x * w, lm[self.LEFT_EYE_OUTER].y * h])
            left_iris_left = np.array([lm[self.LEFT_IRIS_LEFT].x * w, lm[self.LEFT_IRIS_LEFT].y * h])
            left_iris_right = np.array([lm[self.LEFT_IRIS_RIGHT].x * w, lm[self.LEFT_IRIS_RIGHT].y * h])
            left_iris_width = np.linalg.norm(left_iris_right - left_iris_left) + 1e-6
            left_ratio = np.linalg.norm(left_iris_left - left_eye_outer) / left_iris_width

            right_eye_outer = np.array([lm[self.RIGHT_EYE_OUTER].x * w, lm[self.RIGHT_EYE_OUTER].y * h])
            right_iris_right = np.array([lm[self.RIGHT_IRIS_RIGHT].x * w, lm[self.RIGHT_IRIS_RIGHT].y * h])
            right_iris_left = np.array([lm[self.RIGHT_IRIS_LEFT].x * w, lm[self.RIGHT_IRIS_LEFT].y * h])
            right_iris_width = np.linalg.norm(right_iris_right - right_iris_left) + 1e-6
            right_ratio = np.linalg.norm(right_eye_outer - right_iris_right) / right_iris_width

            left_gaze = "LEFT" if left_ratio < 0.48 else "CENTER"
            right_gaze = "RIGHT" if right_ratio < 0.48 else "CENTER"
            gaze_direction = "LEFT" if left_gaze == "LEFT" else "RIGHT" if right_gaze == "RIGHT" else "CENTER"


            # 상하 시선 분석 (눈 크기 변화 기반)
            eye_top = lm[159].y
            eye_bottom = lm[145].y
            eye_opening = abs(eye_top - eye_bottom)

            if eye_opening < self.blink_threshold:
                self.blink_cooldown_counter = self.blink_cooldown_frames
                gaze_vertical = self.gaze_state
            elif self.blink_cooldown_counter > 0:
                self.blink_cooldown_counter -= 1
                gaze_vertical = self.gaze_state
            else:
                if not self.is_calibrated:
                    self.calibration_openings.append(eye_opening)
                    self.frame_idx += 1
                    if self.frame_idx == 30:
                        avg_opening = np.mean(self.calibration_openings)
                        self.up_thresh = avg_opening * 1.1
                        self.down_thresh = avg_opening * 0.9
                        self.is_calibrated = True
                    gaze_vertical = "CENTER"
                else:
                    if eye_opening > self.up_thresh:
                        gaze_vertical = "UP"
                    elif eye_opening < self.down_thresh:
                        gaze_vertical = "DOWN"
                    else:
                        gaze_vertical = "CENTER"

            # 시선 유지 시간
            now = time.time()
            if gaze_vertical != self.gaze_state:
                if self.gaze_state:
                    self.gaze_duration_dict[self.gaze_state] += now - gaze_start_time
                gaze_start_time = now
                self.gaze_state = gaze_vertical

            gaze_result = f"Gaze: {gaze_direction} / {gaze_vertical}"
            
            # 고개 pitch 분석
            image_points = np.array([
                [lm[1].x * w, lm[1].y * h],
                [lm[152].x * w, lm[152].y * h],
                [lm[33].x * w, lm[33].y * h],
                [lm[263].x * w, lm[263].y * h],
                [lm[78].x * w, lm[78].y * h],
                [lm[308].x * w, lm[308].y * h]
            ], dtype=np.float32)

            camera_matrix = self.get_camera_matrix(w, h)
            dist_coeffs = np.zeros((4, 1))

            success, rotation_vector, translation_vector = cv2.solvePnP(
                self.model_points, image_points, camera_matrix, dist_coeffs
            )

            if success:
                rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
                pitch = np.degrees(np.arcsin(-rotation_matrix[2][1]))
                if pitch < -11:
                    pitch_result = "UP"
                elif pitch > 5:
                    pitch_result = "DOWN"
                else:
                    pitch_result = "CENTER"

        if pose_result.pose_landmarks:
            pose_lm = pose_result.pose_landmarks.landmark

            try:
                # 고개 방향 판단
                left_eye_center = lm[self.LEFT_EYE_CENTER]
                right_eye_center = lm[self.RIGHT_EYE_CENTER]
                left_ear = pose_lm[self.LEFT_EAR]
                right_ear = pose_lm[self.RIGHT_EAR]

                left_eye_to_ear = abs(left_eye_center.x - left_ear.x)
                right_eye_to_ear = abs(right_eye_center.x - right_ear.x)
                if left_eye_to_ear > right_eye_to_ear + 0.03:
                    head_result = "LEFT TURN"
                elif right_eye_to_ear > left_eye_to_ear + 0.03:
                    head_result = "RIGHT TURN"
                else:
                    head_result = "CENTER"

                # 어깨 기울기 판단
                diff = pose_lm[self.LEFT_SHOULDER].y - pose_lm[self.RIGHT_SHOULDER].y
                if diff > 0.012:
                    shoulder_result = "LEFT SHOULDER UP"
                elif diff < -0.012:
                    shoulder_result = "RIGHT SHOULDER UP"
                else:
                    shoulder_result = "STRAIGHT"

                # 손 등 얼굴, 어깨 이외 부분 여부 판단
                if pose_lm[self.LEFT_INDEX].visibility > 0.5 or pose_lm[self.RIGHT_INDEX].visibility > 0.5:
                    hand_result = "Appearance"
            except:
                pass

        return {
            "gaze": gaze_result,
            "head": head_result,
            "pitch" : pitch_result,
            "shoulder": shoulder_result,
            "hand" : hand_result
        }

