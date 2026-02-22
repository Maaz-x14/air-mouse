# gesture_detector.py
import cv2
import mediapipe as mp
from dataclasses import dataclass
from typing import Optional, Tuple, Any
from config import PINCH_THRESHOLD, FIST_FINGER_THRESHOLD

@dataclass
class GestureResult:
    gesture: str              # "move", "click", "scroll", "pause", "none"
    index_tip: Optional[Tuple[float, float]]   # (x, y) normalized [0,1]
    landmarks: Any            # Full landmark list for drawing (NormalizedLandmarkList)

class GestureDetector:
    """MediaPipe hand detection & gesture classification."""
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

    def detect(self, frame) -> GestureResult:
        """Process a frame and return detected gesture and landmarks.
        
        Args:
            frame: OpenCV BGR frame.
            
        Returns:
            GestureResult with gesture label, index tip coordinates, and raw landmarks.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb_frame)

        if not result.multi_hand_landmarks:
            return GestureResult("none", None, None)

        hand_landmarks = result.multi_hand_landmarks[0]
        landmarks = hand_landmarks.landmark
        
        # Extract index tip
        index_tip = (landmarks[8].x, landmarks[8].y)
        
        # Classify gesture
        gesture = self._classify_gesture(landmarks)
        
        return GestureResult(gesture, index_tip, hand_landmarks)

    def _classify_gesture(self, landmarks) -> str:
        """Determine gesture based on hand landmarks."""
        def is_extended(tip: int, pip: int) -> bool:
            return landmarks[tip].y < landmarks[pip].y
            
        index_extended = is_extended(8, 6)
        middle_extended = is_extended(12, 10)
        ring_extended = is_extended(16, 14)
        pinky_extended = is_extended(20, 18)
        
        # Pinch
        dx = landmarks[4].x - landmarks[8].x
        dy = landmarks[4].y - landmarks[8].y
        pinch_dist = (dx**2 + dy**2) ** 0.5
        if pinch_dist < PINCH_THRESHOLD:
            return "click"
            
        # Fist
        if (landmarks[8].y > landmarks[5].y and
            landmarks[12].y > landmarks[9].y and
            landmarks[16].y > landmarks[13].y and
            landmarks[20].y > landmarks[17].y):
            return "pause"
            
        # Two fingers (scroll)
        if index_extended and middle_extended and not ring_extended and not pinky_extended:
            return "scroll"
            
        # Index point (move)
        if index_extended and not middle_extended and not ring_extended and not pinky_extended:
            return "move"
            
        return "none"
