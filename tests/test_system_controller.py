from unittest.mock import patch, MagicMock
from system_controller import SystemController

def test_volume_up_calls_pactl():
    ctrl = SystemController()
    ctrl.HAS_PACTL = True
    ctrl.HAS_AMIXER = False
    
    with patch("subprocess.run") as mock_run:
        ctrl.set_volume("up")
        mock_run.assert_any_call(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"],
            check=True, capture_output=True
        )

def test_switch_app_respects_cooldown():
    ctrl = SystemController()
    # Mock pyautogui inside
    with patch('system_controller.pyautogui.hotkey') as mock_hotkey:
        res1 = ctrl.switch_app("next")
        res2 = ctrl.switch_app("next")  # Should be blocked
        assert res1 == True
        assert res2 == False
        assert mock_hotkey.call_count == 1

def test_brightness_fallback_to_xrandr():
    ctrl = SystemController()
    ctrl.HAS_BRIGHTNESSCTL = False
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="HDMI-1 connected\n", returncode=0)
        ctrl.set_brightness("right")
        # Verify xrandr was called twice: once for query, once for set
        assert mock_run.call_count == 2
        
        args = mock_run.call_args_list[1][0][0]
        assert args[0] == "xrandr"
        assert args[1] == "--output"
        assert args[2] == "HDMI-1"
