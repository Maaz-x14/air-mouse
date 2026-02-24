# Implementation Plan
## Air Mouse v1.1 — Volume, Brightness, App Switcher + Bug Fix

---

### Overview

This plan covers **only the delta from v1.0 to v1.1**. All v1.0 phases are complete. This plan begins where the shipped MVP left off.

---

### Phase Overview

| Phase | Name | Goal | Est. Time |
|-------|------|------|-----------|
| 0 | Bug Fix | Fix cursor X-axis inversion | 10 min |
| 1 | Infrastructure | Add system_controller.py, update GestureResult, add VelocityTracker | 45 min |
| 2 | Volume Control | Open palm vertical gesture controls system volume | 45 min |
| 3 | Brightness Control | Open palm horizontal slow gesture controls brightness | 45 min |
| 4 | App Switcher | Open palm fast horizontal flick triggers Alt+Tab | 30 min |
| 5 | Disambiguation & Tuning | Ensure 3 palm gestures don't conflict | 30 min |
| 6 | Overlay & Polish | Update debug HUD, test all features together | 30 min |
| 7 | Tests & Docs | New tests, update README | 30 min |

---

### Phase 0 — Bug Fix: Cursor X-Axis Inversion

**File to edit:** `cursor_controller.py`

**Change:**
```python
# Find the line where target_x is computed. Change:
target_x = int(index_tip.x * self.screen_width)

# To:
target_x = int((1 - index_tip.x) * self.screen_width)
```

This single change fixes horizontal cursor inversion. The Y axis does not need to change.

**Verify:** Run `main.py`, move index finger right → cursor should move right.

**Exit Criteria:** Cursor direction matches finger direction on both axes.

---

### Phase 1 — Infrastructure Updates

#### 1a — Extend `GestureResult` dataclass (`gesture_detector.py`)

Add fields to carry palm movement data:

```python
@dataclass
class GestureResult:
    gesture: str
    index_tip: tuple | None
    palm_center: tuple | None    # ADD: (x, y) normalized
    delta_x: float               # ADD: frame-over-frame X delta of palm
    delta_y: float               # ADD: frame-over-frame Y delta of palm
    velocity: float              # ADD: magnitude of movement this frame
    landmarks: list | None
```

#### 1b — Add `VelocityTracker` to `utils.py`

```python
class VelocityTracker:
    def __init__(self, smoothing: float = 0.4):
        self.prev_pos = None
        self.smooth_velocity = 0.0
        self.smoothing = smoothing

    def update(self, pos: tuple) -> tuple[float, float, float]:
        if self.prev_pos is None:
            self.prev_pos = pos
            return 0.0, 0.0, 0.0
        dx = pos[0] - self.prev_pos[0]
        dy = pos[1] - self.prev_pos[1]
        raw_vel = (dx**2 + dy**2) ** 0.5
        self.smooth_velocity = (
            self.smoothing * raw_vel + (1 - self.smoothing) * self.smooth_velocity
        )
        self.prev_pos = pos
        return dx, dy, self.smooth_velocity

    def reset(self):
        self.prev_pos = None
        self.smooth_velocity = 0.0
```

#### 1c — Create `system_controller.py`

Scaffold the class with method stubs first, then implement per phase:

```python
import subprocess
import shutil
import logging
import pyautogui
from config import VOLUME_STEP, BRIGHTNESS_STEP, SWIPE_COOLDOWN_MS

class SystemController:
    def __init__(self):
        self.HAS_PACTL = shutil.which("pactl") is not None
        self.HAS_AMIXER = shutil.which("amixer") is not None
        self.HAS_BRIGHTNESSCTL = shutil.which("brightnessctl") is not None
        self._log_available_backends()
        self._last_swipe_time = 0

    def _log_available_backends(self): ...
    def set_volume(self, direction: str) -> int: ...
    def set_brightness(self, direction: str) -> int: ...
    def switch_app(self, direction: str) -> None: ...
```

**Exit Criteria:** `system_controller.py` imports cleanly, no errors. All gesture fields populate in `GestureResult`.

---

### Phase 2 — Volume Control

**Files to edit:** `gesture_detector.py`, `system_controller.py`, `main.py`, `config.py`

#### 2a — Open Palm Detection

Add `_is_open_palm()` to `GestureDetector`:

```python
def _is_open_palm(self, landmarks) -> bool:
    """Detect all 5 fingers extended."""
    finger_pairs = [(8, 6), (12, 10), (16, 14), (20, 18)]
    fingers_up = all(landmarks[tip].y < landmarks[pip].y for tip, pip in finger_pairs)
    # Thumb: check x-axis (for right hand, tip should be to the left of knuckle)
    thumb_up = landmarks[4].x < landmarks[3].x
    return fingers_up and thumb_up
```

#### 2b — Update Gesture Classification

In `_classify_gesture()`, after checking fist/pinch/two-fingers/index:

```python
if self._is_open_palm(landmarks):
    # Gesture will be refined by main.py using delta values
    # Return "palm" and let SystemController decide volume vs brightness vs switch
    return "palm"
```

Alternatively, pass delta values into the classifier and classify fully there (preferred):

```python
if self._is_open_palm(landmarks):
    if velocity > SWIPE_VELOCITY_THRESHOLD:
        return "app_switch"
    abs_dx, abs_dy = abs(delta_x), abs(delta_y)
    if abs_dy > abs_dx * AXIS_DOMINANCE_RATIO:
        return "volume"
    if abs_dx > abs_dy * AXIS_DOMINANCE_RATIO:
        return "brightness"
    return "palm_idle"  # Palm visible but not moving enough to classify
```

This requires passing `delta_x`, `delta_y`, `velocity` into `_classify_gesture()`.

#### 2c — Volume Action

Implement `SystemController.set_volume()`:

```python
def set_volume(self, direction: str) -> int:
    change = f"+{VOLUME_STEP}%" if direction == "up" else f"-{VOLUME_STEP}%"
    try:
        if self.HAS_PACTL:
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", change],
                check=True, capture_output=True
            )
            return self._get_volume_pactl()
        elif self.HAS_AMIXER:
            amixer_change = f"{VOLUME_STEP}%+" if direction == "up" else f"{VOLUME_STEP}%-"
            subprocess.run(["amixer", "set", "Master", amixer_change], check=True)
            return -1  # amixer parsing optional
    except Exception as e:
        logging.warning(f"Volume control failed: {e}")
    return -1

def _get_volume_pactl(self) -> int:
    """Parse current volume % from pactl output."""
    try:
        result = subprocess.run(
            ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
            capture_output=True, text=True
        )
        # Output: "Volume: front-left: 65536 / 100% / ..."
        import re
        match = re.search(r"(\d+)%", result.stdout)
        return int(match.group(1)) if match else -1
    except Exception:
        return -1
```

#### 2d — Debounce Volume Triggers

In `main.py`, track the accumulated Y delta since last volume trigger:

```python
volume_delta_accumulator = 0.0

# In loop:
if result.gesture == "volume":
    volume_delta_accumulator += result.delta_y
    if abs(volume_delta_accumulator) > VOLUME_MOVEMENT_THRESHOLD:
        direction = "down" if volume_delta_accumulator > 0 else "up"
        # Note: delta_y positive = hand moved down (image coords)
        last_volume = system_ctrl.set_volume(direction)
        volume_delta_accumulator = 0.0  # reset after trigger
else:
    volume_delta_accumulator = 0.0  # reset if gesture changes
```

**Exit Criteria:** Raise open palm slowly → volume increases. Lower palm → volume decreases. No false triggers from other gestures.

---

### Phase 3 — Brightness Control

**Files to edit:** `system_controller.py`, `config.py`

#### 3a — Detect `brightnessctl` availability

Already done in `SystemController.__init__()` via `shutil.which("brightnessctl")`.

Install check to inform user at startup:
```
INFO: Brightness backend: brightnessctl ✓
```
If not found:
```
WARNING: brightnessctl not found. Install with: sudo apt install brightnessctl
WARNING: Falling back to xrandr (software brightness only)
```

#### 3b — Implement `set_brightness()`

```python
def set_brightness(self, direction: str) -> int:
    try:
        if self.HAS_BRIGHTNESSCTL:
            change = "+5%" if direction == "right" else "5%-"
            subprocess.run(["brightnessctl", "set", change], check=True, capture_output=True)
            return self._get_brightness_brightnessctl()
        else:
            return self._set_brightness_xrandr(direction)
    except Exception as e:
        logging.warning(f"Brightness control failed: {e}")
    return -1

def _get_brightness_brightnessctl(self) -> int:
    try:
        result = subprocess.run(
            ["brightnessctl", "get"], capture_output=True, text=True
        )
        max_result = subprocess.run(
            ["brightnessctl", "max"], capture_output=True, text=True
        )
        current = int(result.stdout.strip())
        maximum = int(max_result.stdout.strip())
        return int((current / maximum) * 100)
    except Exception:
        return -1

def _set_brightness_xrandr(self, direction: str) -> int:
    """Fallback software brightness via xrandr."""
    # Get current connected display name
    try:
        result = subprocess.run(
            ["xrandr", "--query"], capture_output=True, text=True
        )
        import re
        connected = re.findall(r"(\S+) connected", result.stdout)
        if not connected:
            return -1
        display = connected[0]
        # Track brightness in a simple file or instance variable
        self._xrandr_brightness = getattr(self, "_xrandr_brightness", 1.0)
        step = 0.05
        self._xrandr_brightness = max(0.2, min(1.0,
            self._xrandr_brightness + (step if direction == "right" else -step)
        ))
        subprocess.run(
            ["xrandr", "--output", display, "--brightness",
             f"{self._xrandr_brightness:.2f}"],
            check=True
        )
        return int(self._xrandr_brightness * 100)
    except Exception as e:
        logging.warning(f"xrandr brightness failed: {e}")
        return -1
```

#### 3c — Brightness Debounce in main.py

Same pattern as volume — accumulate delta_x before triggering:

```python
brightness_delta_accumulator = 0.0

if result.gesture == "brightness":
    brightness_delta_accumulator += result.delta_x
    if abs(brightness_delta_accumulator) > BRIGHTNESS_MOVEMENT_THRESHOLD:
        direction = "right" if brightness_delta_accumulator > 0 else "left"
        last_brightness = system_ctrl.set_brightness(direction)
        brightness_delta_accumulator = 0.0
else:
    brightness_delta_accumulator = 0.0
```

**Exit Criteria:** Slow palm left → screen dims. Slow palm right → screen brightens. Does not conflict with app switch gesture.

---

### Phase 4 — App Switcher

**Files to edit:** `system_controller.py`, `main.py`, `config.py`

#### 4a — Implement `switch_app()`

```python
import time

def switch_app(self, direction: str) -> bool:
    """Trigger Alt+Tab with cooldown guard.

    Returns:
        True if switch was triggered, False if blocked by cooldown.
    """
    now = time.time() * 1000  # ms
    if now - self._last_swipe_time < SWIPE_COOLDOWN_MS:
        return False
    self._last_swipe_time = now
    try:
        if direction == "next":
            pyautogui.hotkey("alt", "tab")
        else:
            pyautogui.hotkey("alt", "shift", "tab")
        return True
    except Exception as e:
        logging.warning(f"App switch failed: {e}")
        return False
```

#### 4b — App Switch Label in main.py

```python
app_switch_label = ""
app_switch_label_expiry = 0.0

if result.gesture == "app_switch":
    direction = "next" if result.delta_x > 0 else "prev"
    triggered = system_ctrl.switch_app(direction)
    if triggered:
        app_switch_label = "→ App Switch" if direction == "next" else "← App Switch"
        app_switch_label_expiry = time.time() + 1.0  # show for 1 second

# In overlay drawing:
label_to_show = app_switch_label if time.time() < app_switch_label_expiry else ""
```

**Exit Criteria:** Fast palm flick right → windows cycle forward. Fast flick left → cycle backward. No trigger during slow brightness swipes.

---

### Phase 5 — Disambiguation & Threshold Tuning

This phase ensures the 3 palm-based gestures (volume, brightness, app_switch) don't bleed into each other.

**Key Separation Logic:**

```
Open Palm detected → compute delta_x, delta_y, velocity

if velocity > SWIPE_VELOCITY_THRESHOLD:
    → "app_switch"   ← Fast flick wins over everything

elif |delta_y| > |delta_x| * AXIS_DOMINANCE_RATIO:
    → "volume"       ← Clear vertical dominance

elif |delta_x| > |delta_y| * AXIS_DOMINANCE_RATIO:
    → "brightness"   ← Clear horizontal dominance

else:
    → "palm_idle"    ← Ambiguous direction, wait
```

**Recommended starting values (tune during testing):**
- `SWIPE_VELOCITY_THRESHOLD = 0.08` — if too sensitive, increase to 0.12
- `AXIS_DOMINANCE_RATIO = 2.0` — if brightness/volume bleed, increase to 3.0
- `VOLUME_MOVEMENT_THRESHOLD = 0.03` — smaller = more sensitive
- `SWIPE_COOLDOWN_MS = 800` — prevents double-switch on one flick

**Testing matrix:**

| Action | Expected Gesture | Should NOT trigger |
|--------|-----------------|-------------------|
| Slow raise hand | volume | brightness, app_switch |
| Slow lower hand | volume | brightness, app_switch |
| Slow move right | brightness | volume, app_switch |
| Slow move left | brightness | volume, app_switch |
| Fast flick right | app_switch | brightness |
| Fast flick left | app_switch | brightness |
| Hold palm still | palm_idle | anything |

**Exit Criteria:** All 7 rows in the testing matrix pass reliably 9/10 times.

---

### Phase 6 — Debug Overlay & Polish

**Updates to `utils.py` / `main.py`:**

1. Show volume % in corner when volume gesture active:
   ```
   🔊 72%
   ```

2. Show brightness % when brightness gesture active:
   ```
   ☀ 55%
   ```

3. Flash app switch label in center of frame for 1 second:
   ```
   → App Switch
   ```

4. Update gesture label to include new gesture names

5. On startup, print tool availability summary to terminal:
   ```
   [INFO] Air Mouse v1.1 starting...
   [INFO] Volume backend:     pactl ✓
   [INFO] Brightness backend: brightnessctl ✓
   [INFO] App Switch:         pyautogui ✓
   [INFO] Camera index:       0
   ```

---

### Phase 7 — Tests & Documentation

#### New Tests

**`tests/test_system_controller.py`**
```python
from unittest.mock import patch, MagicMock
from system_controller import SystemController

def test_volume_up_calls_pactl():
    ctrl = SystemController()
    with patch("subprocess.run") as mock_run:
        ctrl.set_volume("up")
        mock_run.assert_called_with(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"],
            check=True, capture_output=True
        )

def test_switch_app_respects_cooldown():
    ctrl = SystemController()
    ctrl.switch_app("next")
    result = ctrl.switch_app("next")  # Should be blocked
    assert result == False

def test_brightness_fallback_to_xrandr():
    ctrl = SystemController()
    ctrl.HAS_BRIGHTNESSCTL = False
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="HDMI-1 connected\n", returncode=0)
        ctrl.set_brightness("right")
        # Verify xrandr was called
```

**`tests/test_velocity_tracker.py`**
```python
from utils import VelocityTracker

def test_initial_update_returns_zero():
    tracker = VelocityTracker()
    dx, dy, vel = tracker.update((0.5, 0.5))
    assert dx == 0.0 and dy == 0.0 and vel == 0.0

def test_movement_detected():
    tracker = VelocityTracker()
    tracker.update((0.5, 0.5))
    dx, dy, vel = tracker.update((0.6, 0.5))
    assert dx > 0
    assert vel > 0

def test_reset_clears_state():
    tracker = VelocityTracker()
    tracker.update((0.5, 0.5))
    tracker.update((0.6, 0.5))
    tracker.reset()
    dx, dy, vel = tracker.update((0.7, 0.5))
    assert vel == 0.0
```

#### README Updates

Add to the gesture table:

| Gesture | Action |
|---------|--------|
| Open palm + move up | Volume up |
| Open palm + move down | Volume down |
| Open palm + slow move right | Brightness up |
| Open palm + slow move left | Brightness down |
| Open palm + fast flick right | Next window (Alt+Tab) |
| Open palm + fast flick left | Previous window (Alt+Shift+Tab) |

Add to Known Limitations:
- `brightnessctl` must be installed for hardware brightness control (`sudo apt install brightnessctl`). Without it, software brightness via `xrandr` is used (affects display gamma, not actual backlight).
- App switching may behave differently on tiling window managers.

---

### Landmark Reference (v1.0, unchanged)

```
Wrist: 0
Thumb:  1-2-3-4   (tip=4)
Index:  5-6-7-8   (tip=8,  pip=6)
Middle: 9-10-11-12 (tip=12, pip=10)
Ring:   13-14-15-16 (tip=16, pip=14)
Pinky:  17-18-19-20 (tip=20, pip=18)
Palm center: avg(landmark[0], landmark[9])
```

---

### Risk & Mitigation (v1.1 additions)

| Risk | Mitigation |
|------|------------|
| `pactl` not available | Fallback to `amixer`; log warning at startup |
| `brightnessctl` not available | Fallback to `xrandr`; log warning |
| Wayland breaks `xrandr` | Document; suggest running under X11 session |
| Volume/brightness/switch gestures conflict | `AXIS_DOMINANCE_RATIO` + velocity threshold + `palm_idle` state |
| App switch fires during brightness swipe | Velocity threshold gates it; tune `SWIPE_VELOCITY_THRESHOLD` |
| brightnessctl needs sudo | Add user to `video` group: `sudo usermod -aG video $USER` |