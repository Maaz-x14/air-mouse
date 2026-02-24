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
