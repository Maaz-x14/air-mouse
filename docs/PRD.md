# Product Requirements Document (PRD)
## Air Mouse — Vision-Based Gesture Interaction

---

### 1. Overview

**Product Name:** Air Mouse
**Version:** 1.1
**Platform:** Linux (Ubuntu/Debian-based)
**Language:** Python 3.9+

Air Mouse is a computer vision application that allows users to control their OS cursor and system functions using hand gestures detected via a webcam — no physical input device required.

---

### 2. Problem Statement

Traditional input devices (mouse, trackpad) require physical contact. Air Mouse enables touchless control of the cursor and system settings using natural hand gestures, useful for presentations, accessibility, or demonstrating real CV skills.

---

### 3. Version History

| Version | Features |
|---------|----------|
| 1.0 MVP | Cursor move, pinch click, two-finger scroll, fist pause |
| 1.1 | + Volume control, Brightness control, App switcher (Alt+Tab), cursor X-axis bug fix |

---

### 4. v1.0 Features (Shipped)

- Cursor movement via index finger
- Left click via pinch (thumb + index)
- Scroll via two-finger gesture
- Pause tracking via fist

---

### 5. v1.1 New Features

#### FR-V1: Volume Control
- **Gesture:** Open palm (all 5 fingers extended), move hand **vertically**
- **Action:** Hand moving up → volume increases; hand moving down → volume decreases
- **Implementation:** Use `pactl set-sink-volume @DEFAULT_SINK@ +5%` / `-5%` via `subprocess`. Fallback: `amixer set Master 5%+` / `5%-`
- **Sensitivity:** Configurable `VOLUME_STEP` (default: 5%)
- **Debounce:** Trigger only when cumulative vertical delta exceeds `VOLUME_MOVEMENT_THRESHOLD` (default: 0.03 normalized units) since last trigger
- **Feedback:** Debug overlay shows current volume percentage

#### FR-B1: Brightness Control
- **Gesture:** Open palm (all 5 fingers extended), move hand **horizontally** — slow, deliberate movement
- **Disambiguation from Volume:** Compare absolute movement deltas each frame. If `|delta_y| > |delta_x|` → volume mode. If `|delta_x| > |delta_y|` → brightness mode. Require dominant axis to be at least 2x larger than minor axis for clean separation.
- **Action:** Hand moving right → brightness increases; hand moving left → brightness decreases
- **Implementation:** Primary: `brightnessctl set +5%` / `5%-`. Fallback: `xrandr --output <display> --brightness <value>` (0.1 to 1.0 range)
- **Sensitivity:** Configurable `BRIGHTNESS_STEP` (default: 5%)
- **Feedback:** Debug overlay shows current brightness percentage

#### FR-A1: App Switcher (Alt+Tab)
- **Gesture:** Open palm + fast horizontal flick (velocity-based trigger)
- **Distinction from Brightness:** Brightness responds to slow, sustained movement. App Switcher triggers on a sudden velocity spike — specifically when the palm's horizontal velocity exceeds `SWIPE_VELOCITY_THRESHOLD` (default: 0.08 normalized units/frame)
- **Action:** Fast flick right → `Alt+Tab`; Fast flick left → `Alt+Shift+Tab`
- **Implementation:** `pyautogui.hotkey('alt', 'tab')` / `pyautogui.hotkey('alt', 'shift', 'tab')`
- **Debounce:** `SWIPE_COOLDOWN_MS` minimum between triggers (default: 800ms) to prevent accidental repeat fires
- **Feedback:** Debug overlay briefly shows "→ App Switch" or "← App Switch" label for 1 second

---

### 6. Bug Fix: Cursor X-Axis Flip

**Issue:** Cursor moves opposite to finger's horizontal direction.
**Root Cause:** MediaPipe returns raw (unmirrored) camera coordinates. The debug window displays a horizontally flipped feed, but the coordinate mapping was not accounting for this inversion.
**Fix (in `cursor_controller.py`):**
```python
# WRONG — causes inverted X movement:
screen_x = int(index_tip.x * SCREEN_WIDTH)

# CORRECT — mirrors the coordinate to match display:
screen_x = int((1 - index_tip.x) * SCREEN_WIDTH)
```

---

### 7. Complete Gesture Table (v1.1)

| Gesture | Detection Logic | Action |
|---------|----------------|--------|
| Index Point | Only index finger extended | Move cursor |
| Pinch | Distance(thumb tip, index tip) < PINCH_THRESHOLD | Left click |
| Two Fingers | Index + middle extended, others closed | Scroll |
| Fist | All 4 fingers closed (tips below MCP joints) | Pause tracking |
| Open Palm + slow vertical move | All 5 extended, delta_y dominant | Volume up/down |
| Open Palm + slow horizontal move | All 5 extended, delta_x dominant, low velocity | Brightness up/down |
| Open Palm + fast horizontal flick | All 5 extended, horizontal velocity > threshold | App switch (Alt+Tab) |

---

### 8. Technical Stack (v1.1)

| Component | Library / Tool |
|-----------|----------------|
| Camera capture | OpenCV (`cv2`) |
| Hand tracking | MediaPipe (`mediapipe`) |
| OS mouse control | PyAutoGUI (`pyautogui`) |
| Coordinate math | NumPy (`numpy`) |
| Volume control | `pactl` via `subprocess` (fallback: `amixer`) |
| Brightness control | `brightnessctl` via `subprocess` (fallback: `xrandr`) |
| App switching | `pyautogui.hotkey()` |

---

### 9. Performance Requirements

- Gesture detection latency: < 100ms
- Camera feed: 30 FPS target
- Volume/brightness: max 10 updates/sec via debounce
- App switch: 800ms cooldown minimum between triggers
- CPU usage: < 50% on a modern dual-core

---

### 10. Non-Goals (v1.1)

- No right-click or drag
- No multi-hand support
- No virtual keyboard
- No Windows/macOS support

---

### 11. Success Metrics (v1.1)

- Cursor X-axis no longer inverted ✅
- Open palm raised/lowered changes system volume ✅
- Open palm moved left/right slowly changes brightness ✅
- Fast horizontal flick triggers Alt+Tab ✅
- Slow vs fast palm movements cleanly disambiguated ✅
- All v1.0 features continue to work ✅