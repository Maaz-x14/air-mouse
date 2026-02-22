# Coding Guidelines
## Air Mouse — Vision-Based Gesture Interaction MVP

---

### 1. Language & Environment

- **Python 3.9+** strictly
- Use a **virtual environment**: `python3 -m venv venv && source venv/bin/activate`
- All dependencies pinned in `requirements.txt`

```
opencv-python>=4.8.0
mediapipe>=0.10.0
pyautogui>=0.9.54
numpy>=1.24.0
```

---

### 2. Project Structure

```
air_mouse/
├── main.py                  # Entry point
├── gesture_detector.py      # MediaPipe hand detection & gesture classification
├── cursor_controller.py     # Coordinate mapping + PyAutoGUI mouse control
├── config.py                # All tunable constants
├── utils.py                 # Helper functions (smoothing, drawing)
├── requirements.txt
├── README.md
└── docs/
    ├── PRD.md
    ├── Coding_Guidelines.md
    └── Implementation_Plan.md
```

---

### 3. Code Style

- Follow **PEP 8** strictly
- Max line length: **88 characters** (Black formatter standard)
- Use **type hints** on all function signatures
- Use **docstrings** on all classes and public methods (Google style)
- No magic numbers — all constants go in `config.py`

**Example:**
```python
def map_to_screen(value: float, screen_dim: int) -> int:
    """Map a normalized MediaPipe coordinate to screen pixels.

    Args:
        value: Normalized coordinate [0.0, 1.0] from MediaPipe.
        screen_dim: Screen dimension in pixels (width or height).

    Returns:
        Integer pixel coordinate clamped to screen bounds.
    """
    return int(np.clip(value * screen_dim, 0, screen_dim - 1))
```

---

### 4. Configuration (`config.py`)

All tunable values must live here. Never hardcode in logic files.

```python
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
SCROLL_SPEED = 20             # Pixels per scroll tick
FIST_FINGER_THRESHOLD = 0.1   # Max tip-to-palm distance for fist

# Smoothing
SMOOTHING_FACTOR = 0.5        # 0 = no smoothing, 1 = full lag (exponential)

# Debug
SHOW_DEBUG_WINDOW = True
DRAW_LANDMARKS = True
SHOW_GESTURE_LABEL = True
```

---

### 5. Gesture Detection Module (`gesture_detector.py`)

- Wrap MediaPipe `Hands` in a class: `GestureDetector`
- Expose a single method: `detect(frame) -> GestureResult`
- `GestureResult` should be a dataclass:

```python
@dataclass
class GestureResult:
    gesture: str              # "move", "click", "scroll", "pause", "none"
    index_tip: tuple | None   # (x, y) normalized [0,1]
    landmarks: list | None    # Full landmark list for drawing
```

- Gesture classification logic must be in its own private method `_classify_gesture()`

---

### 6. Cursor Controller Module (`cursor_controller.py`)

- Wrap PyAutoGUI in a class: `CursorController`
- Apply **exponential moving average** smoothing:
  ```
  smooth_x = alpha * target_x + (1 - alpha) * prev_x
  ```
- Use `pyautogui.FAILSAFE = False` with a comment explaining why
- Debounce clicks: minimum 300ms between consecutive clicks

---

### 7. Error Handling

- **Camera not found**: Print clear error message and exit gracefully
- **MediaPipe init failure**: Catch and log, exit with code 1
- **PyAutoGUI exceptions**: Log and continue (don't crash on single frame)
- Use `try/except` around the main loop for clean `Ctrl+C` shutdown

---

### 8. Logging

- Use Python's built-in `logging` module (not `print` in production code)
- Log level: `INFO` by default, `DEBUG` for landmark coordinates
- Format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`

---

### 9. Testing

- Write at least one unit test per module in `tests/`
- Use `pytest`
- Mock camera and PyAutoGUI in tests (no real hardware needed)

---

### 10. Git Conventions

- Commit messages: `type(scope): description`  
  e.g. `feat(gesture): add pinch click detection`
- Branch per feature: `feature/pinch-click`, `feature/scroll`
- Never commit `venv/` or `__pycache__/`

---

### 11. README Requirements

The `README.md` must include:
- Setup instructions
- How to run
- Gesture reference table
- Known limitations
- Screenshot or GIF demo placeholder
