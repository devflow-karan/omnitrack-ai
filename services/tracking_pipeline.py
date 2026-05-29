import cv2
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from detection import HandDetector, FaceDetector
from gestures import GestureRecognizer
from utils import FPSCounter
from config import settings

class TrackingPipeline:
    def __init__(self) -> None:
        self.hand_detector = HandDetector()
        self.face_detector = FaceDetector()
        self.gesture_recognizer = GestureRecognizer()
        self.fps_counter = FPSCounter()
        
        self.frame_count = 0
        self.cached_results: Dict[str, Any] = {"faces": [], "hands": [], "fps": 0.0}

    def initialize(self) -> None:
        """
        Initializes detectors and starts the FPS counter.
        """
        self.hand_detector.initialize()
        self.face_detector.initialize()
        self.fps_counter.start()

    def process_frame(self, frame: np.ndarray, draw: bool = True) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Run the frame through face, hand tracking, and gesture recognition.
        :param frame: BGR NumPy array from camera source.
        :param draw: Boolean whether to draw overlay visuals on the output frame.
        :return: (processed_frame, results_metadata_dict)
        """
        self.frame_count += 1
        
        # Performance optimization: frame skip check
        if settings.FRAME_SKIP > 1 and (self.frame_count % settings.FRAME_SKIP != 0):
            # Return annotated frame using cached coordinates if draw=True, or just return original
            annotated_frame = frame.copy()
            if draw:
                self.face_detector.draw_landmarks(annotated_frame, self.cached_results["faces"])
                self.hand_detector.draw_landmarks(annotated_frame, self.cached_results["hands"])
            
            # Update FPS and return cached results
            fps = self.fps_counter.update()
            results = self.cached_results.copy()
            results["fps"] = round(fps, 1)
            return annotated_frame, results

        # 1. Process Hand Tracking and gesture classification
        hands_data = self.hand_detector.process(frame)
        for hand in hands_data:
            gesture_results = self.gesture_recognizer.process(hand)
            # Merge gesture classification details into hand data
            hand.update(gesture_results)

        # 2. Process Face Tracking (mesh, head pose, blink, mouth, gaze)
        faces_data = self.face_detector.process(frame)

        # 3. Calculate current pipeline FPS
        fps = self.fps_counter.update()

        # Compile results payload
        results = {
            "faces": faces_data,
            "hands": hands_data,
            "fps": round(fps, 1)
        }

        # Cache results for frame skipping
        self.cached_results = results

        # 4. Draw visualizations on frame if requested
        annotated_frame = frame.copy()
        if draw:
            self.face_detector.draw_landmarks(annotated_frame, faces_data)
            self.hand_detector.draw_landmarks(annotated_frame, hands_data)
            
            # Overlay pipeline FPS on top-left of the image
            cv2.putText(
                annotated_frame, 
                f"FPS: {results['fps']}", 
                (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (0, 255, 0), 
                2, 
                cv2.LINE_AA
            )

        return annotated_frame, results

    def close(self) -> None:
        """
        Closes MediaPipe model objects.
        """
        self.hand_detector.close()
        self.face_detector.close()
