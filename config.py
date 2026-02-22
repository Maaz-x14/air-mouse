# config.py

# Camera
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Screen
SCREEN_WIDTH = 1920   # Auto-detected at runtime preferred
SCREEN_HEIGHT = 1080

# Gesture Thresholds
PINCH_THRESHOLD = 0.05        # Normalized distance for pinch detection
SCROLL_SPEED = 10             # Pixels per scroll tick
FIST_FINGER_THRESHOLD = 0.1   # Max tip-to-palm distance for fist

# Smoothing
SMOOTHING_FACTOR = 0.5        # 0 = no smoothing, 1 = full lag (exponential)

# Debug
SHOW_DEBUG_WINDOW = True
DRAW_LANDMARKS = True
SHOW_GESTURE_LABEL = True
