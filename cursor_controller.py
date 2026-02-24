# cursor_controller.py
import pyautogui
import logging
import time
from typing import Optional
from utils import map_to_screen, smooth
from config import SCREEN_WIDTH, SCREEN_HEIGHT, SMOOTHING_FACTOR, SCROLL_SPEED

class CursorController:
    """Controls OS cursor movement and actions via PyAutoGUI."""
    def __init__(self):
        self.logger = logging.getLogger("AirMouse.CursorController")
        # FailSafe is disabled to prevent crashes when moving coordinates to the edge of the screen
        pyautogui.FAILSAFE = False
        
        try:
            self.screen_width, self.screen_height = pyautogui.size()
        except Exception:
            self.screen_width = SCREEN_WIDTH
            self.screen_height = SCREEN_HEIGHT
        
        self.prev_x = 0
        self.prev_y = 0
        self.first_move = True
        
        self.last_click_time = 0.0
        self.debounce_time = 3.0  # 3 seconds debounce
        
        # for scroll
        self.prev_scroll_y_norm: Optional[float] = None
        
    def move(self, index_tip_x: float, index_tip_y: float):
        """Move cursor based on normalized index tip coordinate."""
        target_x = int(index_tip_x * self.screen_width)
        target_y = int(index_tip_y * self.screen_height)
        
        if self.first_move:
            self.prev_x = target_x
            self.prev_y = target_y
            self.first_move = False
            
        smooth_x = int(smooth(self.prev_x, target_x, SMOOTHING_FACTOR))
        smooth_y = int(smooth(self.prev_y, target_y, SMOOTHING_FACTOR))
        
        self.prev_x = smooth_x
        self.prev_y = smooth_y
        
        try:
            pyautogui.moveTo(smooth_x, smooth_y)
        except Exception as e:
            self.logger.warning(f"Failed to move mouse: {e}")

    def click(self):
        """Trigger a left click with debounce."""
        current_time = time.time()
        if (current_time - self.last_click_time) > self.debounce_time:
            try:
                pyautogui.click()
                self.last_click_time = current_time
                self.logger.info("Left click triggered")
            except Exception as e:
                self.logger.warning(f"Failed to click: {e}")

    def scroll(self, index_tip_y: float):
        """Trigger scroll based on vertical delta."""
        if self.prev_scroll_y_norm is None:
            self.prev_scroll_y_norm = index_tip_y
            return
            
        delta_y = index_tip_y - self.prev_scroll_y_norm
        
        # Ticking threshold to avoid micro scrolls
        if abs(delta_y) > 0.005:  # lowered threshold for smoother response
            try:
                if delta_y < 0:
                    # Finger moved up -> scroll up
                    pyautogui.scroll(SCROLL_SPEED)
                else:
                    # Finger moved down -> scroll down
                    pyautogui.scroll(-SCROLL_SPEED)
                # Reset reference to new position
                self.prev_scroll_y_norm = index_tip_y
            except Exception as e:
                self.logger.warning(f"Failed to scroll: {e}")
                
    def reset_scroll(self):
        """Reset scroll state when gesture stops."""
        self.prev_scroll_y_norm = None
