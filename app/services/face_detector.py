import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
from typing import Tuple

from app.models.schemas import FaceData, BoundingBox, Orientation, DeepFaceAttributes, HandData, Point3D
from app.services.tracking import CentroidTracker
from app.services.inference import deep_worker
from app.utils.smoothing import TemporalSmoother, EmotionSmoother
from app.utils.geometry import estimate_head_pose

class AdvancedFaceDetector:
    def __init__(self):
        # Initialize Face Landmarker
        base_options_face = python.BaseOptions(model_asset_path='app/models/face_landmarker.task')
        options_face = vision.FaceLandmarkerOptions(
            base_options=base_options_face,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=True,
            num_faces=5
        )
        self.detector = vision.FaceLandmarker.create_from_options(options_face)
        
        # Initialize Gesture Recognizer (Hand Tracking)
        base_options_hand = python.BaseOptions(model_asset_path='app/models/gesture_recognizer.task')
        options_hand = vision.GestureRecognizerOptions(
            base_options=base_options_hand,
            num_hands=2
        )
        self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options_hand)

        self.tracker = CentroidTracker()
        
        # We need smoothers per face ID
        self.age_smoothers = {}
        self.emotion_smoothers = {}

    def process_frame(self, frame: np.ndarray) -> Tuple[list[FaceData], list[HandData]]:
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # 1. Process Faces
        face_results = self.detector.detect(mp_image)
        face_data_list = []
        rects = []
        orientations_list = []
        smiles_list = []
        h, w, _ = frame.shape

        if face_results.face_landmarks:
            for face_idx, face_landmarks in enumerate(face_results.face_landmarks):
                # Compute Bounding Box
                x_coords = [lm.x * w for lm in face_landmarks]
                y_coords = [lm.y * h for lm in face_landmarks]
                
                x_min, x_max = int(min(x_coords)), int(max(x_coords))
                y_min, y_max = int(min(y_coords)), int(max(y_coords))
                
                # Expand bounding box heavily for DeepFace context
                box_w = x_max - x_min
                box_h = y_max - y_min
                
                pad_w = int(box_w * 0.4)
                pad_h = int(box_h * 0.4)
                
                x_min = max(0, x_min - pad_w)
                y_min = max(0, y_min - pad_h)
                x_max = min(w, x_max + pad_w)
                y_max = min(h, y_max + pad_h)
                
                rects.append((x_min, y_min, x_max - x_min, y_max - y_min))
                
                # Compute Orientation (Fix OpenCV Crash: extract only 6 canonical points)
                target_indices = [1, 152, 263, 33, 291, 61]
                points_2d = np.array([(face_landmarks[idx].x * w, face_landmarks[idx].y * h) for idx in target_indices])
                pitch, yaw, roll, rvec, tvec = estimate_head_pose(points_2d, (h, w))
                
                orientations_list.append(Orientation(pitch=pitch, yaw=yaw, roll=roll))
                
                # Heuristic for smile (mouth width vs lower face height)
                mouth_width = np.linalg.norm(points_2d[4] - points_2d[5])
                lower_face_height = np.linalg.norm(points_2d[0] - points_2d[1])
                smiles_list.append(mouth_width > lower_face_height * 0.85)

        # Update Face Tracker
        objects = self.tracker.update(rects)

        # Process each tracked face
        for object_id, centroid in objects.items():
            matched_rect = None
            matched_orientation = Orientation(pitch=0, yaw=0, roll=0)
            matched_smiling = False
            
            min_dist = float("inf")
            for i, (rx, ry, rw, rh) in enumerate(rects):
                cx = rx + rw / 2.0
                cy = ry + rh / 2.0
                dist = (cx - centroid[0])**2 + (cy - centroid[1])**2
                if dist < min_dist:
                    min_dist = dist
                    matched_rect = (rx, ry, rw, rh)
                    matched_orientation = orientations_list[i]
                    matched_smiling = smiles_list[i]

            if matched_rect is None:
                continue

            rx, ry, rw, rh = matched_rect
            crop = frame[ry:ry+rh, rx:rx+rw]
            
            if crop.size > 0:
                deep_worker.enqueue_crop(object_id, crop)

            cached_attr = deep_worker.get_cached_attributes(object_id)
            
            if object_id not in self.age_smoothers:
                self.age_smoothers[object_id] = TemporalSmoother(alpha=0.1)
                self.emotion_smoothers[object_id] = EmotionSmoother(history_size=10)
                
            age = None
            gender = None
            emotion = None
            is_deep_stale = True

            if cached_attr:
                raw_age = cached_attr.get("age")
                if raw_age:
                    age = int(self.age_smoothers[object_id].update(raw_age))
                
                raw_emotion = cached_attr.get("emotion")
                if raw_emotion:
                    emotion = self.emotion_smoothers[object_id].update(raw_emotion)
                    
                gender = cached_attr.get("gender")
                
                if time.time() - cached_attr["timestamp"] < 2.0:
                    is_deep_stale = False
            
            # Override emotion if landmark heuristic strongly indicates a smile
            if matched_smiling:
                emotion = "happy"

            face_data = FaceData(
                face_id=object_id,
                bbox=BoundingBox(x=rx, y=ry, w=rw, h=rh),
                orientation=matched_orientation,
                deep_attributes=DeepFaceAttributes(age=age, gender=gender, emotion=emotion),
                is_deep_stale=is_deep_stale
            )
            face_data_list.append(face_data)

        # Cleanup smoothers
        for obj_id in list(self.age_smoothers.keys()):
            if obj_id not in self.tracker.objects:
                del self.age_smoothers[obj_id]
                del self.emotion_smoothers[obj_id]

        # 2. Process Hands & Gestures
        hand_results = self.gesture_recognizer.recognize(mp_image)
        hand_data_list = []
        
        if hand_results.hand_landmarks:
            for i, landmarks in enumerate(hand_results.hand_landmarks):
                handedness = hand_results.handedness[i][0].category_name if hand_results.handedness else "Unknown"
                gesture = hand_results.gestures[i][0].category_name if hand_results.gestures and hand_results.gestures[i] else "None"
                pts = [Point3D(x=lm.x, y=lm.y, z=lm.z) for lm in landmarks]
                
                # Fallback heuristic for back-hand fist (MediaPipe struggles with this) and Thumb Up mixup
                if gesture in ["None", "Thumb_Up"]:
                    wrist = np.array([pts[0].x, pts[0].y, pts[0].z])
                    fingers_curled = True
                    # Compare distance of fingertips to wrist vs MCP (knuckles) to wrist
                    for tip_idx, mcp_idx in [(8, 5), (12, 9), (16, 13), (20, 17)]:
                        tip = np.array([pts[tip_idx].x, pts[tip_idx].y, pts[tip_idx].z])
                        mcp = np.array([pts[mcp_idx].x, pts[mcp_idx].y, pts[mcp_idx].z])
                        if np.linalg.norm(tip - wrist) > np.linalg.norm(mcp - wrist):
                            fingers_curled = False
                            break
                    if fingers_curled:
                        # Check thumb extension to distinguish Fist from Thumb Up
                        thumb_tip = np.array([pts[4].x, pts[4].y, pts[4].z])
                        index_mcp = np.array([pts[5].x, pts[5].y, pts[5].z])
                        wrist_to_mcp_dist = np.linalg.norm(index_mcp - wrist)
                        thumb_to_index_dist = np.linalg.norm(thumb_tip - index_mcp)
                        
                        if thumb_to_index_dist > wrist_to_mcp_dist * 0.8:
                            gesture = "Thumb_Up"
                        else:
                            gesture = "Closed_Fist"
                
                hand_data_list.append(HandData(
                    handedness=handedness,
                    gesture=gesture,
                    landmarks=pts
                ))

        return face_data_list, hand_data_list

    def close(self):
        self.detector.close()
        self.gesture_recognizer.close()
