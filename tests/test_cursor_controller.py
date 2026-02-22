import pytest
import sys
from unittest.mock import patch, MagicMock

# Mock pyautogui before it is imported to avoid tkinter dependency error on Linux
sys.modules['pyautogui'] = MagicMock()

from cursor_controller import CursorController
from utils import map_to_screen, smooth

def test_map_to_screen():
    assert map_to_screen(0.5, 1000) == 500
    assert map_to_screen(0.0, 1000) == 0
    assert map_to_screen(1.0, 1000) == 999
    
    assert map_to_screen(0.0, 1000, invert=True) == 999
    assert map_to_screen(1.0, 1000, invert=True) == 0

def test_smooth():
    assert smooth(100.0, 200.0, 0.5) == 150.0
    assert smooth(100.0, 200.0, 1.0) == 200.0
    assert smooth(100.0, 200.0, 0.0) == 100.0

@patch('cursor_controller.pyautogui')
def test_cursor_controller_move(mock_pyautogui):
    mock_pyautogui.size.return_value = (1920, 1080)
    controller = CursorController()
    
    # first move
    controller.move(0.5, 0.5)
    assert mock_pyautogui.moveTo.called

@patch('cursor_controller.pyautogui')
def test_cursor_controller_click(mock_pyautogui):
    controller = CursorController()
    
    # Initial click should succeed
    controller.click()
    assert mock_pyautogui.click.called
    
    # Debounce check
    mock_pyautogui.click.reset_mock()
    controller.click()
    assert not mock_pyautogui.click.called
