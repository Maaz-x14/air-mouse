# Product Requirements Document (PRD)
## Air Mouse — Vision-Based Gesture Interaction MVP

---

### 1. Overview

**Product Name:** Air Mouse  
**Version:** 1.0 MVP  
**Platform:** Linux (Ubuntu/Debian-based)  
**Language:** Python 3.9+

Air Mouse is a computer vision application that allows users to control their OS mouse cursor using hand gestures detected via a webcam — no physical mouse required.

---

### 2. Problem Statement

Traditional input devices (mouse, trackpad) require physical contact. Air Mouse enables touchless control of the cursor using natural hand gestures, useful for presentations, accessibility, or just building impressive CV projects.

---

### 3. Goals

- Control mouse cursor by moving index finger in front of webcam
- Trigger left click via pinch gesture (index + thumb)
- Enable scroll via two-finger gesture
- Pause tracking via fist gesture
- Smooth, low-latency response with minimal jitter

---

### 4. Non-Goals (MVP Scope Limits)

- No multi-hand support
- No right-click or drag support (post-MVP)
- No GUI settings panel (post-MVP)
- No support for Windows/macOS (post-MVP)

---

### 5. User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US1 | User | Move my index finger to control cursor | I can navigate without a mouse |
| US2 | User | Pinch to click | I can select items |
| US3 | User | Use two fingers to scroll | I can scroll pages |
| US4 | User | Make a fist to pause tracking | I can reposition my hand without moving cursor |

---

### 6. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1 | Detect hand landmarks using MediaPipe | Must Have |
| FR2 | Map index fingertip to screen coordinates | Must Have |
| FR3 | Apply smoothing to cursor movement | Must Have |
| FR4 | Detect pinch gesture → left click | Must Have |
| FR5 | Detect two-finger gesture → scroll | Should Have |
| FR6 | Detect fist gesture → pause tracking | Should Have |
| FR7 | Display annotated camera feed (debug view) | Should Have |
| FR8 | Show gesture label overlay on feed | Nice to Have |

---

### 7. Gesture Definitions

| Gesture | Detection Logic | Action |
|---------|----------------|--------|
| Index Point | Only index finger extended | Move cursor |
| Pinch | Distance between thumb tip & index tip < threshold | Left click |
| Two Fingers | Index + middle finger extended, others closed | Scroll |
| Fist | All fingers closed | Pause tracking |

---

### 8. Technical Stack

| Component | Library |
|-----------|---------|
| Camera capture | OpenCV (`cv2`) |
| Hand tracking | MediaPipe (`mediapipe`) |
| OS mouse control | PyAutoGUI (`pyautogui`) |
| Coordinate math | NumPy (`numpy`) |

---

### 9. Performance Requirements

- Gesture detection latency: < 100ms
- Camera feed: 30 FPS target
- Cursor smoothing: interpolation factor configurable (default 0.5)
- CPU usage: < 40% on a modern dual-core

---

### 10. Success Metrics (MVP)

- Cursor moves accurately with index finger ✅
- Click fires on pinch within 200ms ✅
- Scroll works with two fingers ✅
- Fist pauses tracking cleanly ✅
- Application runs without crashes for 5+ minutes ✅
