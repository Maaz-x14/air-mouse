# Air Mouse

Air Mouse is a Linux computer vision MVP that allows touchless OS interaction through natural hand gestures.

## Setup

1. Check camera indices with `python camera_test.py`
2. Create and set up a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Update `CAMERA_INDEX` in `config.py` if needed.

## Usage

```bash
python main.py
```

Press `q` on the open window or `Ctrl+C` in the terminal to exit.

## Gestures

| Gesture | Action | 
|---------|--------|
| Index finger pointing up | Move cursor |
| Pinch thumb & index finger | Left click |
| Index & middle fingers up | Scroll |
| Fist (all fingers closed) | Pause tracking |
| Open palm + move up | Volume up |
| Open palm + move down | Volume down |
| Open palm + slow move right | Brightness up |
| Open palm + slow move left | Brightness down |
| Open palm + fast flick right | Next window (Alt+Tab) |
| Open palm + fast flick left | Previous window (Alt+Shift+Tab) |

## Known Limitations

- **brightnessctl**: Must be installed for hardware brightness control (`sudo apt install brightnessctl`). Without it, software brightness via `xrandr` is used (affects display gamma, not actual backlight).
- **App Switching**: May behave differently on tiling window managers.
- **Wayland**: PyAutoGUI may have bugs on default Wayland sessions (mouse control might be jittery or not work). If so, run with `DISPLAY=:0`.
- Single hand only.
- Smoothing can cause slight cursor lag; adjust `SMOOTHING_FACTOR` in `config.py` for faster response.

![Placeholder Demo](https://via.placeholder.com/800x450.png?text=Air+Mouse+Demo)
