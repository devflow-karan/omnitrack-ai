import numpy as np
import time
from typing import Dict, List, Any, Tuple, Optional

class GestureRecognizer:
    def __init__(self, history_len: int = 5, velocity_threshold: float = 150.0) -> None:
        """
        Initializes the Gesture Recognizer.
        :param history_len: Number of frames to track for velocity.
        :param velocity_threshold: Threshold in pixels/second to count as active movement.
        """
        self.history_len = history_len
        self.velocity_threshold = velocity_threshold

        # History structure: { "Left": [(x, y, timestamp)], "Right": [(x, y, timestamp)] }
        self.history: Dict[str, List[Tuple[float, float, float]]] = {"Left": [], "Right": []}

    def process(self, hand_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies gestures and calculates movement velocity/direction for a single hand.
        """
        label = hand_data["label"]
        lm_pixel = hand_data["landmarks_pixel"]
        fingers = hand_data["fingers"]
        angles = hand_data["angles"]

        if len(lm_pixel) < 21:
            return {"gesture": "Unknown", "velocity": 0.0, "direction": "Static"}

        # 1. Classify Gesture using rule-based thresholds on finger angles and open states
        gesture = self._classify_gesture(fingers, angles, lm_pixel)

        # 2. Track Wrist Position, Velocity, and Direction
        wrist = lm_pixel[0] # Wrist coordinate (x, y)
        current_time = time.perf_counter()
        
        wrist_pos = (float(wrist["x"]), float(wrist["y"]))
        
        # Append to history
        self.history[label].append((*wrist_pos, current_time))
        if len(self.history[label]) > self.history_len:
            self.history[label].pop(0)

        # Calculate Velocity & Direction
        velocity, direction = self._calculate_velocity_and_direction(label)

        return {
            "gesture": gesture,
            "velocity": round(velocity, 1),
            "direction": direction
        }

    def _classify_gesture(self, fingers: Dict[str, bool], angles: Dict[str, float], lm_pixel: List[Dict[str, Any]]) -> str:
        """
        Rules-based classification of gestures based on finger states and key distances.
        """
        thumb = fingers["thumb"]
        index = fingers["index"]
        middle = fingers["middle"]
        ring = fingers["ring"]
        pinky = fingers["pinky"]

        # Calculate Euclidean distances for pinching gestures
        # Tip landmarks: Thumb Tip (4), Index Tip (8), Middle Tip (12)
        pt_thumb_tip = np.array([lm_pixel[4]["x"], lm_pixel[4]["y"]])
        pt_index_tip = np.array([lm_pixel[8]["x"], lm_pixel[8]["y"]])
        pt_middle_tip = np.array([lm_pixel[12]["x"], lm_pixel[12]["y"]])
        
        dist_thumb_index = float(np.linalg.norm(pt_thumb_tip - pt_index_tip))
        dist_thumb_middle = float(np.linalg.norm(pt_thumb_tip - pt_middle_tip))

        # Check distances relative to the size of the hand (represented by wrist to index MCP distance)
        pt_wrist = np.array([lm_pixel[0]["x"], lm_pixel[0]["y"]])
        pt_index_mcp = np.array([lm_pixel[5]["x"], lm_pixel[5]["y"]])
        hand_scale = float(np.linalg.norm(pt_index_mcp - pt_wrist)) + 1e-6

        norm_thumb_index = dist_thumb_index / hand_scale
        norm_thumb_middle = dist_thumb_middle / hand_scale

        # 1. OK Sign: Thumb and index tips touching, middle, ring, pinky extended
        # norm distance threshold typically < 0.25
        if norm_thumb_index < 0.25 and middle and ring and pinky:
            return "OK"

        # 2. Pinch / Click: Index and Thumb tips extremely close, others are tucked (closed)
        if norm_thumb_index < 0.15 and not middle and not ring and not pinky:
            return "Pinch_Click"

        # 3. Fist: All closed
        if not thumb and not index and not middle and not ring and not pinky:
            return "Fist"

        # 4. Open Palm: All extended
        if thumb and index and middle and ring and pinky:
            return "Open_Palm"

        # 5. Peace Sign: Index and Middle extended, Ring and Pinky closed
        if index and middle and not ring and not pinky:
            return "Peace"

        # 6. Thumbs Up: Thumb extended, others closed
        # Thumb IP angle (or extension) is open
        if thumb and not index and not middle and not ring and not pinky:
            # We also check if hand is oriented such that thumb is upright, 
            # but simple state-check suffices for basic classification
            return "Thumbs_Up"

        # 7. Pointing: Index extended, others closed
        if index and not middle and not ring and not pinky:
            return "Point"

        # 8. Spiderman / Rock: Index, Pinky, and Thumb extended; Middle and Ring closed
        if index and pinky and thumb and not middle and not ring:
            return "Rock_On"

        return "Unknown"

    def _calculate_velocity_and_direction(self, label: str) -> Tuple[float, str]:
        """
        Calculates hand movement velocity (pixels per second) and maps to directions.
        """
        hist = self.history[label]
        if len(hist) < 2:
            return 0.0, "Static"

        # First and last elements in history window
        x0, y0, t0 = hist[0]
        xn, yn, tn = hist[-1]

        dt = tn - t0
        if dt <= 0:
            return 0.0, "Static"

        # Calculate distances
        dx = xn - x0
        dy = yn - y0
        distance = np.sqrt(dx**2 + dy**2)

        # Velocity in pixels/sec
        velocity = distance / dt

        # Direction calculation if velocity exceeds threshold
        if velocity > self.velocity_threshold:
            # Check dominant movement dimension
            if abs(dx) > abs(dy):
                direction = "Right" if dx > 0 else "Left"
            else:
                direction = "Down" if dy > 0 else "Up" # Screen y increases downwards
        else:
            direction = "Static"

        return velocity, direction
