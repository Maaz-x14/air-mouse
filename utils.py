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
