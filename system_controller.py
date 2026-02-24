import subprocess
import shutil
import logging
import time
import pyautogui
from config import VOLUME_STEP, BRIGHTNESS_STEP, SWIPE_COOLDOWN_MS

class SystemController:
    """Handles volume, brightness, and window management via subprocess."""
    def __init__(self):
        self.HAS_PACTL = shutil.which("pactl") is not None
        self.HAS_AMIXER = shutil.which("amixer") is not None
        self.HAS_BRIGHTNESSCTL = shutil.which("brightnessctl") is not None
        self._last_swipe_time = 0.0
        self._log_available_backends()

    def _log_available_backends(self):
        logging.info("Volume backend pactl: %s", "✓" if self.HAS_PACTL else "✗")
        logging.info("Volume backend amixer: %s", "✓" if self.HAS_AMIXER else "✗")
        logging.info("Brightness backend brightnessctl: %s", "✓" if self.HAS_BRIGHTNESSCTL else "✗ (will use xrandr)")
        logging.info("App Switch PyAutoGUI: ✓")

    def set_volume(self, direction: str) -> int:
        """Adjust system volume up or down.

        Args:
            direction: "up" or "down"

        Returns:
            Current volume percentage after adjustment, or -1 on failure.
        """
        change = f"+{VOLUME_STEP}%" if direction == "up" else f"-{VOLUME_STEP}%"
        try:
            if self.HAS_PACTL:
                subprocess.run(
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", change],
                    check=True, capture_output=True
                )
                return self._get_volume_pactl()
            elif self.HAS_AMIXER:
                amixer_change = f"{VOLUME_STEP}%+" if direction == "up" else f"{VOLUME_STEP}%-"
                subprocess.run(["amixer", "set", "Master", amixer_change], check=True)
                return -1  # amixer parsing optional
        except Exception as e:
            logging.warning(f"Volume control failed: {e}")
        return -1

    def _get_volume_pactl(self) -> int:
        """Parse current volume % from pactl output."""
        try:
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True
            )
            import re
            # Output: "Volume: front-left: 65536 / 100% / ..."
            match = re.search(r"(\d+)%", result.stdout)
            return int(match.group(1)) if match else -1
        except Exception:
            return -1

    def set_brightness(self, direction: str) -> int:
        """Adjust screen brightness up or down.

        Args:
            direction: "right" (up) or "left" (down)

        Returns:
            Current brightness percentage after adjustment, or -1 on failure.
        """
        try:
            if self.HAS_BRIGHTNESSCTL:
                change = f"+{BRIGHTNESS_STEP}%" if direction == "right" else f"{BRIGHTNESS_STEP}%-"
                subprocess.run(["brightnessctl", "set", change], check=True, capture_output=True)
                return self._get_brightness_brightnessctl()
            else:
                return self._set_brightness_xrandr(direction)
        except Exception as e:
            logging.warning(f"Brightness control failed: {e}")
        return -1

    def _get_brightness_brightnessctl(self) -> int:
        try:
            result = subprocess.run(
                ["brightnessctl", "get"], capture_output=True, text=True
            )
            max_result = subprocess.run(
                ["brightnessctl", "max"], capture_output=True, text=True
            )
            current = int(result.stdout.strip())
            maximum = int(max_result.stdout.strip())
            return int((current / maximum) * 100)
        except Exception:
            return -1

    def _set_brightness_xrandr(self, direction: str) -> int:
        """Fallback software brightness via xrandr."""
        # Get current connected display name
        try:
            result = subprocess.run(
                ["xrandr", "--query"], capture_output=True, text=True
            )
            import re
            connected = re.findall(r"(\S+) connected", result.stdout)
            if not connected:
                return -1
            display = connected[0]
            # Track brightness in a simple file or instance variable
            self._xrandr_brightness = getattr(self, "_xrandr_brightness", 1.0)
            step = BRIGHTNESS_STEP / 100.0
            self._xrandr_brightness = max(0.2, min(1.0,
                self._xrandr_brightness + (step if direction == "right" else -step)
            ))
            subprocess.run(
                ["xrandr", "--output", display, "--brightness",
                 f"{self._xrandr_brightness:.2f}"],
                check=True
            )
            return int(self._xrandr_brightness * 100)
        except Exception as e:
            logging.warning(f"xrandr brightness failed: {e}")
            return -1

    def switch_app(self, direction: str) -> bool:
        """Trigger Alt+Tab with cooldown guard.

        Returns:
            True if switch was triggered, False if blocked by cooldown.
        """
        now = time.time() * 1000  # ms
        if now - self._last_swipe_time < SWIPE_COOLDOWN_MS:
            return False
        self._last_swipe_time = now
        try:
            if direction == "next":
                pyautogui.hotkey("alt", "tab")
            else:
                pyautogui.hotkey("alt", "shift", "tab")
            return True
        except Exception as e:
            logging.warning(f"App switch failed: {e}")
            return False
