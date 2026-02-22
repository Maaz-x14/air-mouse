# main.py
import cv2
import mediapipe as mp
import logging
import sys
import time

from gesture_detector import GestureDetector
from cursor_controller import CursorController
from config import (
    CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT, 
    SHOW_DEBUG_WINDOW, DRAW_LANDMARKS, SHOW_GESTURE_LABEL
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AirMouse")

def main() -> None:
    """Entry point for the Air Mouse application.
    
    Initializes the camera, gesture detector, and cursor controller,
    then runs the main processing loop to read frames, detect hand
    landmarks, and control the OS cursor.
    """
    logger.info("Starting Air Mouse application...")
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    if not cap.isOpened():
        logger.error(f"Could not open camera at index {CAMERA_INDEX}")
        sys.exit(1)

    detector = GestureDetector()
    controller = CursorController()
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_hands = mp.solutions.hands

    # Variables for FPS calculation
    prev_time = 0
    tracking_active = True

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
            elif tracking_active == False and result.gesture != "none":
                # Resume tracking when hand opens (any gesture other than pause/none)
                tracking_active = True
                
            if tracking_active:
                if result.gesture == "move" and result.index_tip:
                    controller.move(result.index_tip[0], result.index_tip[1])
                elif result.gesture == "click":
                    controller.click()
                elif result.gesture == "scroll" and result.index_tip:
                    controller.scroll(result.index_tip[1])
            
            if SHOW_DEBUG_WINDOW:
                display_frame = frame.copy()
                
                # Draw colored circle on index fingertip
                if result.index_tip:
                    # Map to screen dimensions for the opencv circle
                    cam_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    cam_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    cx = int(result.index_tip[0] * cam_w)
                    cy = int(result.index_tip[1] * cam_h)
                    
                    color = (0, 255, 0) if tracking_active else (0, 0, 255)
                    cv2.circle(display_frame, (cx, cy), 15, color, cv2.FILLED)

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
                
                # Overlays
                cv2.putText(display_frame, f"FPS: {int(fps)}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                if SHOW_GESTURE_LABEL:
                    cv2.putText(display_frame, f"Gesture: {result.gesture}", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                
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
