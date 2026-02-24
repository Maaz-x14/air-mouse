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
SCROLL_SPEED = 2              # Pixels per scroll tick (smaller for smoother feel)
FIST_FINGER_THRESHOLD = 0.1   # Max tip-to-palm distance for fist

# Volume Control — v1.1
VOLUME_STEP = 5                      # Percent per trigger
VOLUME_MOVEMENT_THRESHOLD = 0.03     # Normalized Y delta to trigger volume change

# Brightness Control — v1.1
BRIGHTNESS_STEP = 5                  # Percent per trigger
BRIGHTNESS_MOVEMENT_THRESHOLD = 0.03 # Normalized X delta to trigger brightness change
AXIS_DOMINANCE_RATIO = 2.0           # |dominant_axis| must be N× the minor axis

# App Switcher — v1.1
SWIPE_VELOCITY_THRESHOLD = 0.04      # Normalized units/frame to classify as a flick
SWIPE_COOLDOWN_MS = 800              # Minimum ms between app-switch triggers

# Smoothing
SMOOTHING_FACTOR = 0.2        # 0 = no smoothing, 1 = full lag (exponential)

# Debug
SHOW_DEBUG_WINDOW = True
DRAW_LANDMARKS = True
SHOW_GESTURE_LABEL = True
