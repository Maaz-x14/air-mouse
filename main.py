# main.py
import cv2
import mediapipe as mp
import logging
import sys
import time

from gesture_detector import GestureDetector
from cursor_controller import CursorController
from system_controller import SystemController
from utils import draw_overlay
from config import (
    CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT, 
    SHOW_DEBUG_WINDOW, DRAW_LANDMARKS, SHOW_GESTURE_LABEL,
    VOLUME_MOVEMENT_THRESHOLD, BRIGHTNESS_MOVEMENT_THRESHOLD
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AirMouse")

def main() -> None:
    """Entry point for the Air Mouse application.
    
    Initializes the camera, gesture detector, and cursor controller,
    then runs the main processing loop to read frames, detect hand
    landmarks, and control the OS cursor.
    """
    logger.info("Starting Air Mouse v1.1 application...")
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    if not cap.isOpened():
        logger.error(f"Could not open camera at index {CAMERA_INDEX}")
        sys.exit(1)

    system_ctrl = SystemController()
    detector = GestureDetector()
    controller = CursorController()
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_hands = mp.solutions.hands

    # Variables for FPS calculation
    prev_time = 0.0
    tracking_active = True
    
    # State variables
    last_volume = -1
    last_brightness = -1
    app_switch_label = ""
    app_switch_label_expiry = 0.0
    
    # Accums
    volume_delta_accumulator = 0.0
    brightness_delta_accumulator = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.error("Camera read failed.")
                break
                
            frame = cv2.flip(frame, 1) # Mirror effect for natural interaction
            
            result = detector.detect(frame)
            
            # Reset scroll logic if not scrolling
            if result.gesture != "scroll":
                controller.reset_scroll()
                
            # Handle Gestures
            if result.gesture == "pause":
                tracking_active = False
            elif tracking_active == False and result.gesture != "none" and result.gesture != "palm_idle":
                # Resume tracking when hand begins doing anything other than pause/none/palm_idle
                tracking_active = True
                
            if tracking_active:
                if result.gesture == "move" and result.index_tip:
                    controller.move(result.index_tip[0], result.index_tip[1])
                elif result.gesture == "click":
                    controller.click()
                elif result.gesture == "scroll" and result.index_tip:
                    controller.scroll(result.index_tip[1])
                elif result.gesture == "volume":
                    volume_delta_accumulator += result.delta_y
                    if abs(volume_delta_accumulator) > VOLUME_MOVEMENT_THRESHOLD:
                        direction = "down" if volume_delta_accumulator > 0 else "up"
                        last_volume = system_ctrl.set_volume(direction)
                        volume_delta_accumulator = 0.0
                elif result.gesture == "brightness":
                    brightness_delta_accumulator += result.delta_x
                    if abs(brightness_delta_accumulator) > BRIGHTNESS_MOVEMENT_THRESHOLD:
                        direction = "right" if brightness_delta_accumulator > 0 else "left"
                        last_brightness = system_ctrl.set_brightness(direction)
                        brightness_delta_accumulator = 0.0
                elif result.gesture == "app_switch":
                    direction = "next" if result.delta_x > 0 else "prev"
                    triggered = system_ctrl.switch_app(direction)
                    if triggered:
                        app_switch_label = "→ App Switch" if direction == "next" else "← App Switch"
                        app_switch_label_expiry = time.time() + 1.0

            # Reset accumulators if gesture changes
            if result.gesture != "volume":
                volume_delta_accumulator = 0.0
            if result.gesture != "brightness":
                brightness_delta_accumulator = 0.0

            if SHOW_DEBUG_WINDOW:
                display_frame = frame.copy()
                
                # Draw landmarks
                if DRAW_LANDMARKS and result.landmarks:
                    mp_drawing.draw_landmarks(
                        display_frame,
                        result.landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                # FPS Calculation
                current_time = time.time()
                fps = 1 / (current_time - prev_time) if prev_time > 0 else 0
                prev_time = current_time

                # Validate app switch label
                label_to_show = app_switch_label if current_time < app_switch_label_expiry else ""

                draw_overlay(
                    display_frame, 
                    result.gesture if SHOW_GESTURE_LABEL else "", 
                    fps, 
                    last_volume, 
                    last_brightness,
                    label_to_show, 
                    tracking_active,
                    result.index_tip
                )
                
                cv2.imshow("Air Mouse", display_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("Quit key pressed.")
                    break
    except KeyboardInterrupt:
        logger.info("Ctrl+C pressed. Gracefully shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        cap.release()
        cv2.destroyAllWindows()
        logger.info("Application shut down.")

if __name__ == "__main__":
    main()
