import pytest
from unittest.mock import patch, MagicMock
from gesture_detector import GestureDetector

class MockLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y

@pytest.fixture
def detector():
    with patch.object(GestureDetector, '__init__', lambda self, *args, **kwargs: None):
        det = GestureDetector()
        return det

def test_classify_gesture_move(detector):
    landmarks = [MockLandmark(0.5, 0.8) for _ in range(21)]
    
    # index extended (y goes down as value increases, tip < pip is extended)
    landmarks[8].y = 0.2
    landmarks[6].y = 0.4
    
    # others folded
    landmarks[12].y = 0.6; landmarks[10].y = 0.4
    landmarks[16].y = 0.6; landmarks[14].y = 0.4
    landmarks[20].y = 0.6; landmarks[18].y = 0.4
    
    # Thumb far
    landmarks[4].x = 0.1; landmarks[8].x = 0.9
    landmarks[4].y = 0.5
    
    # make sure not fist
    landmarks[5].y = 0.45
    landmarks[9].y = 0.45
    landmarks[13].y = 0.45
    landmarks[17].y = 0.45
    
    gesture = detector._classify_gesture(landmarks)
    assert gesture == "move"

def test_classify_gesture_click(detector):
    landmarks = [MockLandmark(0.5, 0.8) for _ in range(21)]
    # others can be whatever, just test pinch dist
    # distance between 4 and 8
    landmarks[4].x = 0.5
    landmarks[4].y = 0.5
    landmarks[8].x = 0.51
    landmarks[8].y = 0.51 # distance ~0.014 < 0.05
    
    gesture = detector._classify_gesture(landmarks)
    assert gesture == "click"

def test_classify_gesture_pause(detector):
    landmarks = [MockLandmark(0.5, 0.8) for _ in range(21)]
    
    # all tips below MCP joints
    landmarks[8].y = 0.9; landmarks[5].y = 0.5
    landmarks[12].y = 0.9; landmarks[9].y = 0.5
    landmarks[16].y = 0.9; landmarks[13].y = 0.5
    landmarks[20].y = 0.9; landmarks[17].y = 0.5
    
    # make sure pinch distance > 0.05
    landmarks[4].x = 0.1
    landmarks[8].x = 0.9
    
    gesture = detector._classify_gesture(landmarks)
    assert gesture == "pause"
