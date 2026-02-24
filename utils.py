# utils.py
import numpy as np

def map_to_screen(value: float, screen_dim: int, invert: bool = False) -> int:
    """Map a normalized MediaPipe coordinate to screen pixels.

    Args:
        value: Normalized coordinate [0.0, 1.0] from MediaPipe.
        screen_dim: Screen dimension in pixels (width or height).
        invert: If True, flips the coordinate (1.0 - value).

    Returns:
        Integer pixel coordinate clamped to screen bounds.
    """
    if invert:
        value = 1.0 - value
    return int(np.clip(value * screen_dim, 0, screen_dim - 1))

def smooth(current: float, target: float, alpha: float) -> float:
    """Apply exponential smoothing mapping.
    
    Args:
        current: Previous smoothed value.
        target: New target value.
        alpha: Smoothing factor weighting the target (0-1).
        
    Returns:
        New smoothed value.
    """
    return alpha * target + (1.0 - alpha) * current

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
        """Reset velocity tracker."""
        self.prev_pos = None
        self.smooth_velocity = 0.0

from typing import Optional, Tuple
import cv2

def draw_overlay(frame, gesture: str, fps: float, volume: int, brightness: int,
                 app_switch_label: str, tracking_active: bool, index_tip: Optional[Tuple[float, float]] = None) -> None:
    """Draw all HUD elements on the debug frame."""
    # FPS counter (top-left)
    cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Gesture label (below FPS)
    cv2.putText(frame, f"Gesture: {gesture}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                
    # Volume %
    if gesture == "volume" and volume != -1:
        cv2.putText(frame, f"Vol: {volume}%", (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
                    
    # Brightness %
    if gesture == "brightness" and brightness != -1:
        cv2.putText(frame, f"Bright: {brightness}%", (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    
    # App switch label
    if app_switch_label:
        # Centered
        h, w = frame.shape[:2]
        size = cv2.getTextSize(app_switch_label, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
        cv2.putText(frame, app_switch_label, ((w - size[0]) // 2, (h + size[1]) // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 255), 3)
                    
    # Tracking indicator dot on index fingertip
    if index_tip:
        h, w = frame.shape[:2]
        cx = int(index_tip[0] * w)
        cy = int(index_tip[1] * h)
        color = (0, 255, 0) if tracking_active else (0, 0, 255)
        cv2.circle(frame, (cx, cy), 15, color, cv2.FILLED)
