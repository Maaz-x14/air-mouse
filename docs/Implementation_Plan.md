# Implementation Plan
## Air Mouse — Vision-Based Gesture Interaction MVP

---

### Phase Overview

| Phase | Name | Goal | Est. Time |
|-------|------|------|-----------|
| 0 | Environment Setup | Camera verified, deps installed | 30 min |
| 1 | Camera + Hand Detection | See hand landmarks on screen | 1 hr |
| 2 | Cursor Movement | Index finger moves cursor | 1 hr |
| 3 | Gesture Detection | Pinch, scroll, fist recognized | 2 hr |
| 4 | Polish & Stability | Smoothing, debounce, debug UI | 1 hr |
| 5 | Testing & Docs | Tests pass, README done | 1 hr |

---

### Phase 0 — Environment & Camera Verification

**Goal:** Confirm the development environment is ready before writing any application code.

**Steps:**
1. Check Linux camera device availability:
   ```bash
   ls /dev/video*
   v4l2-ctl --list-devices
   ```
2. Test camera with OpenCV:
   ```python
   # camera_test.py
   import cv2
   cap = cv2.VideoCapture(0)
   print("Camera opened:", cap.isOpened())
   ret, frame = cap.read()
   print("Frame captured:", ret, "Shape:", frame.shape if ret else "N/A")
   cap.release()
   ```
3. Create and activate virtual environment
4. Install all dependencies from `requirements.txt`
5. Verify imports work:
   ```python
   import cv2, mediapipe, pyautogui, numpy
   print("All imports OK")
   ```

**Exit Criteria:** Camera opens, frame is captured, all imports succeed.

---

### Phase 1 — Camera Feed + Hand Landmark Detection

**Files to create:** `main.py`, `gesture_detector.py`, `config.py`

**Steps:**
1. Create `config.py` with all constants
2. Build `GestureDetector` class with MediaPipe Hands initialized
3. In `main.py`, open camera loop:
   - Read frame
   - Flip frame horizontally (mirror effect)
   - Pass to `GestureDetector.detect()`
   - Draw landmarks on frame using `mp_drawing`
   - Show window with `cv2.imshow()`
   - Exit on `q` key

**Exit Criteria:** Camera window shows live feed with hand skeleton drawn over detected hand.

---

### Phase 2 — Cursor Movement

**Files to create:** `cursor_controller.py`, `utils.py`

**Steps:**
1. Build `CursorController` class
2. Implement `map_to_screen()` coordinate transformation:
   - MediaPipe gives normalized [0,1] coords
   - Multiply by screen dimensions
   - Flip X axis (camera is mirrored)
3. Implement exponential smoothing in `CursorController.move()`
4. In main loop: if gesture is "move", call `cursor_controller.move(index_tip)`
5. Auto-detect screen size using `pyautogui.size()`

**Exit Criteria:** Moving index finger moves cursor smoothly across the screen.

---

### Phase 3 — Gesture Detection & Actions

**Steps:**

#### 3a — Pinch Click
- Calculate Euclidean distance between landmark 4 (thumb tip) and landmark 8 (index tip)
- If distance < `PINCH_THRESHOLD` → call `cursor_controller.click()`
- Implement 300ms debounce to prevent repeat clicks

#### 3b — Two-Finger Scroll
- Check if index (8) and middle (12) tips are both extended above their PIP joints
- Other fingers should be folded
- Call `pyautogui.scroll(SCROLL_SPEED)` or `-SCROLL_SPEED` based on vertical position change

#### 3c — Fist Pause
- Detect fist: all 4 finger tips below their respective MCP joints
- Set `tracking_active = False` → skip mouse move
- Resume tracking when hand opens

**Landmark Reference:**
```
Thumb:  1-2-3-4 (tip=4)
Index:  5-6-7-8 (tip=8)
Middle: 9-10-11-12 (tip=12)
Ring:   13-14-15-16 (tip=16)
Pinky:  17-18-19-20 (tip=20)
```

**Exit Criteria:** All 4 gestures trigger correct actions reliably.

---

### Phase 4 — Polish & Debug UI

**Steps:**
1. Add gesture label text overlay to debug window (top-left corner)
2. Draw colored circle on index fingertip (green = tracking, red = paused)
3. Add FPS counter to debug window
4. Tune `SMOOTHING_FACTOR` and `PINCH_THRESHOLD` for comfort
5. Add graceful `Ctrl+C` shutdown and camera release

**Exit Criteria:** App runs for 5+ minutes without crash, debug view is informative.

---

### Phase 5 — Testing & Documentation

**Steps:**
1. Write `tests/test_gesture_detector.py`:
   - Test gesture classification with mock landmarks
2. Write `tests/test_cursor_controller.py`:
   - Test coordinate mapping math
   - Test smoothing output
3. Complete `README.md` with:
   - Installation steps
   - Usage guide
   - Gesture table
   - Troubleshooting (camera permission, display env var)

**Exit Criteria:** `pytest` passes all tests. README is user-ready.

---

### Key Landmark Math

```python
# Finger extended check: tip.y < pip.y (in image coords, y increases downward)
def is_finger_extended(landmarks, tip_idx: int, pip_idx: int) -> bool:
    return landmarks[tip_idx].y < landmarks[pip_idx].y

# Pinch distance (normalized)
def pinch_distance(landmarks) -> float:
    dx = landmarks[4].x - landmarks[8].x
    dy = landmarks[4].y - landmarks[8].y
    return (dx**2 + dy**2) ** 0.5

# Exponential smoothing
def smooth(current: float, target: float, alpha: float) -> float:
    return alpha * target + (1 - alpha) * current
```

---

### Risk & Mitigation

| Risk | Mitigation |
|------|------------|
| Camera not detected on Linux | Check `/dev/video*`, permissions (`sudo usermod -aG video $USER`) |
| PyAutoGUI fails on Wayland | Set `DISPLAY=:0` or use `xdotool` as fallback |
| High CPU usage | Reduce resolution in config, process every 2nd frame |
| Jittery cursor | Increase `SMOOTHING_FACTOR` |
| Pinch fires accidentally | Increase `PINCH_THRESHOLD` |
