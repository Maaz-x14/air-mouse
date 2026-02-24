# Coding Guidelines
## Air Mouse — Vision-Based Gesture Interaction

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

> Note: Volume, brightness, and app-switch features use Linux CLI tools via `subprocess` — no new Python packages required.

---

### 2. Project Structure (v1.1)

```
air_mouse/
├── main.py                    # Entry point — camera loop, orchestration
├── gesture_detector.py        # MediaPipe detection & gesture classification
├── cursor_controller.py       # Coordinate mapping + PyAutoGUI mouse control
├── system_controller.py       # NEW: Volume, brightness, app-switch actions
├── config.py                  # All tunable constants (updated for v1.1)
├── utils.py                   # Helper functions (smoothing, drawing, velocity)
├── camera_test.py             # Camera diagnostic script
├── requirements.txt
├── README.md
└── docs/
    ├── PRD.md
    ├── Coding_Guidelines.md
    └── Implementation_Plan.md
```

**Key change from v1.0:** All system-level actions (volume, brightness, hotkeys) are isolated in `system_controller.py`. This keeps `cursor_controller.py` focused on mouse-only logic.

---

### 3. Code Style

- Follow **PEP 8** strictly
- Max line length: **88 characters** (Black formatter standard)
- Use **type hints** on all function signatures
- Use **docstrings** on all classes and public methods (Google style)
- No magic numbers — all constants in `config.py`

---

### 4. Configuration (`config.py`) — v1.1 Updates

All tunable values live here. Add v1.1 constants under clearly labeled sections.

```python
# config.py

# Camera
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Screen (auto-detected at runtime preferred)
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Gesture Thresholds — v1.0
PINCH_THRESHOLD = 0.05
SCROLL_SPEED = 20
FIST_FINGER_THRESHOLD = 0.1
SMOOTHING_FACTOR = 0.5

# Volume Control — v1.1
VOLUME_STEP = 5                      # Percent per trigger
VOLUME_MOVEMENT_THRESHOLD = 0.03     # Normalized Y delta to trigger volume change

# Brightness Control — v1.1
BRIGHTNESS_STEP = 5                  # Percent per trigger
BRIGHTNESS_MOVEMENT_THRESHOLD = 0.03 # Normalized X delta to trigger brightness change
AXIS_DOMINANCE_RATIO = 2.0           # |dominant_axis| must be N× the minor axis

# App Switcher — v1.1
SWIPE_VELOCITY_THRESHOLD = 0.08      # Normalized units/frame to classify as a flick
SWIPE_COOLDOWN_MS = 800              # Minimum ms between app-switch triggers

# Debug
SHOW_DEBUG_WINDOW = True
DRAW_LANDMARKS = True
SHOW_GESTURE_LABEL = True
```

---

### 5. Gesture Detection Module (`gesture_detector.py`) — v1.1 Updates

The `GestureResult` dataclass must be extended to carry movement data needed by the new features:

```python
@dataclass
class GestureResult:
    gesture: str               # "move", "click", "scroll", "pause",
                               # "volume", "brightness", "app_switch", "none"
    index_tip: tuple | None    # (x, y) normalized — for cursor control
    palm_center: tuple | None  # (x, y) normalized — for palm-based gestures
    delta_x: float             # Frame-over-frame X movement of palm center
    delta_y: float             # Frame-over-frame Y movement of palm center
    velocity: float            # Magnitude of movement vector this frame
    landmarks: list | None     # Full landmark list for drawing
```

**Palm center calculation:**
```python
# Use the average of wrist (0) and middle finger MCP (9) as a stable palm center
palm_center_x = (landmarks[0].x + landmarks[9].x) / 2
palm_center_y = (landmarks[0].y + landmarks[9].y) / 2
```

**Open palm detection (required for all 3 new gestures):**
```python
def _is_open_palm(self, landmarks) -> bool:
    """All 5 fingers extended."""
    fingers = [
        (8, 6),   # index tip, pip
        (12, 10), # middle
        (16, 14), # ring
        (20, 18), # pinky
    ]
    thumb_extended = landmarks[4].x < landmarks[3].x  # left hand; invert for right
    fingers_extended = all(landmarks[tip].y < landmarks[pip].y for tip, pip in fingers)
    return thumb_extended and fingers_extended
```

**Gesture classification priority order (important — prevents conflicts):**
1. Fist → "pause"
2. Pinch → "click"
3. Two fingers → "scroll"
4. Open palm + high velocity → "app_switch"
5. Open palm + delta_y dominant → "volume"
6. Open palm + delta_x dominant → "brightness"
7. Index only → "move"
8. Default → "none"

---

### 6. System Controller Module (`system_controller.py`) — NEW

Create a new class `SystemController` that wraps all OS-level system calls.

```python
class SystemController:
    """Handles volume, brightness, and window management via subprocess."""

    def set_volume(self, direction: str) -> int:
        """Adjust system volume up or down.

        Args:
            direction: "up" or "down"

        Returns:
            Current volume percentage after adjustment, or -1 on failure.
        """

    def set_brightness(self, direction: str) -> int:
        """Adjust screen brightness up or down.

        Args:
            direction: "up" or "down"

        Returns:
            Current brightness percentage after adjustment, or -1 on failure.
        """

    def switch_app(self, direction: str) -> None:
        """Trigger Alt+Tab or Alt+Shift+Tab.

        Args:
            direction: "next" or "prev"
        """
```

**subprocess patterns to use:**

```python
import subprocess

# Volume — PulseAudio (primary)
subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"], check=False)

# Volume — ALSA fallback
subprocess.run(["amixer", "set", "Master", "5%+"], check=False)

# Get current volume (for overlay display)
result = subprocess.run(
    ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
    capture_output=True, text=True
)
# Parse percentage from output

# Brightness — brightnessctl (primary)
subprocess.run(["brightnessctl", "set", "+5%"], check=False)

# Brightness — xrandr fallback
subprocess.run(
    ["xrandr", "--output", display_name, "--brightness", str(value)],
    check=False
)

# App switch
import pyautogui
pyautogui.hotkey("alt", "tab")
pyautogui.hotkey("alt", "shift", "tab")
```

**Error handling in SystemController:**
- Wrap every `subprocess.run()` in try/except
- Log failures with `logging.warning()` — never crash
- Gracefully fall back (e.g., pactl fails → try amixer)
- Detect available tools at startup with `shutil.which()`:

```python
import shutil

HAS_PACTL = shutil.which("pactl") is not None
HAS_AMIXER = shutil.which("amixer") is not None
HAS_BRIGHTNESSCTL = shutil.which("brightnessctl") is not None
```

---

### 7. Velocity Tracking in `utils.py` — NEW

Add a `VelocityTracker` helper to compute smooth per-frame velocity:

```python
class VelocityTracker:
    """Tracks frame-over-frame movement velocity of a point."""

    def __init__(self, smoothing: float = 0.4):
        self.prev_pos: tuple | None = None
        self.smoothing = smoothing
        self.smooth_velocity: float = 0.0

    def update(self, pos: tuple) -> tuple[float, float, float]:
        """Update with new position.

        Returns:
            Tuple of (delta_x, delta_y, velocity_magnitude)
        """
        if self.prev_pos is None:
            self.prev_pos = pos
            return 0.0, 0.0, 0.0

        dx = pos[0] - self.prev_pos[0]
        dy = pos[1] - self.prev_pos[1]
        velocity = (dx**2 + dy**2) ** 0.5
        self.smooth_velocity = (
            self.smoothing * velocity + (1 - self.smoothing) * self.smooth_velocity
        )
        self.prev_pos = pos
        return dx, dy, self.smooth_velocity

    def reset(self) -> None:
        self.prev_pos = None
        self.smooth_velocity = 0.0
```

---

### 8. Cursor Controller (`cursor_controller.py`) — Bug Fix

**Apply this fix immediately:**

```python
def move(self, index_tip) -> None:
    # FIX: Invert X to correct mirrored camera coordinate
    target_x = int((1 - index_tip.x) * self.screen_width)
    target_y = int(index_tip.y * self.screen_height)
    # ... rest of smoothing logic unchanged
```

---

### 9. Debug Overlay Updates (`utils.py`)

Extend the existing overlay drawing to show v1.1 feedback:

```python
def draw_overlay(frame, gesture: str, fps: float, volume: int, brightness: int,
                 app_switch_label: str, tracking_active: bool) -> None:
    """Draw all HUD elements on the debug frame."""
    # Gesture label (top-left)
    # FPS counter (top-right)
    # Volume bar or % (bottom-left) — only show when gesture == "volume"
    # Brightness bar or % (bottom-left) — only show when gesture == "brightness"
    # App switch label (center) — show for 1 second after trigger, then fade
    # Tracking indicator dot on index fingertip (green=active, red=paused)
```

---

### 10. Main Loop Orchestration (`main.py`) — v1.1 Updates

```python
# Pseudo-code for updated main loop
system_ctrl = SystemController()
velocity_tracker = VelocityTracker()
last_volume = -1
last_brightness = -1
app_switch_label = ""
app_switch_label_timer = 0

while True:
    frame = camera.read()
    result = gesture_detector.detect(frame)

    if result.gesture == "move":
        cursor_ctrl.move(result.index_tip)

    elif result.gesture == "click":
        cursor_ctrl.click()

    elif result.gesture == "scroll":
        cursor_ctrl.scroll(result.delta_y)

    elif result.gesture == "pause":
        pass  # tracking suspended

    elif result.gesture == "volume":
        direction = "up" if result.delta_y < 0 else "down"
        last_volume = system_ctrl.set_volume(direction)

    elif result.gesture == "brightness":
        direction = "right" if result.delta_x > 0 else "left"
        last_brightness = system_ctrl.set_brightness(direction)

    elif result.gesture == "app_switch":
        direction = "next" if result.delta_x > 0 else "prev"
        system_ctrl.switch_app(direction)
        app_switch_label = "→ App Switch" if direction == "next" else "← App Switch"
        app_switch_label_timer = time.time()

    draw_overlay(frame, result.gesture, fps, last_volume, last_brightness,
                 app_switch_label, tracking_active)
```

---

### 11. Error Handling

- Camera not found → clear message, exit code 1
- `pactl`/`brightnessctl` not installed → log warning, disable feature gracefully, inform user
- PyAutoGUI exceptions → log and continue
- `Ctrl+C` → clean shutdown, camera release

---

### 12. Logging

- `logging` module throughout — no bare `print()` in production code
- Level: `INFO` default, `DEBUG` for per-frame landmark data
- Format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Log available system tools at startup:
  ```
  INFO: Volume backend: pactl ✓
  INFO: Brightness backend: brightnessctl ✓
  ```

---

### 13. Testing (v1.1 Additions)

Add tests for new modules:

- `tests/test_system_controller.py`:
  - Mock `subprocess.run`, verify correct commands are called for each direction
  - Test fallback logic (pactl unavailable → amixer)
- `tests/test_velocity_tracker.py`:
  - Test delta calculation correctness
  - Test velocity smoothing output
  - Test app-switch threshold triggering

---

### 14. Git Conventions

- Branch: `feature/volume-control`, `feature/brightness-control`, `feature/app-switcher`, `fix/cursor-x-axis`
- Commit format: `type(scope): description`
  - `fix(cursor): invert X axis coordinate mapping`
  - `feat(volume): add pactl volume control with fallback`
  - `feat(brightness): add brightnessctl brightness control`
  - `feat(app-switch): add velocity-based swipe gesture for Alt+Tab`