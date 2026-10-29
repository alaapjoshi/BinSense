# Intellibin (v1, 2023)

The original hackathon prototype that BinSense grew out of. It's kept here for reference and **is not maintained**. For the working version, see the [main README](../../README.md).

Intellibin tried to sort items three ways, into **trash**, **recycling**, and **compost**, using three 28BYJ-48 stepper motors.

| File | What it does |
|---|---|
| `intellibin_detect.py` | A modified YOLOv5 `detect.py`. After each frame, it substring-matches the detected class names (for example `Non_Biodegradable` or `Biodegradable-Recyclable`) and sends `0`, `1`, or `2` over serial. |
| `firmware/intellibin/intellibin.ino` | Reads the number with `Serial.parseInt()` and turns the matching stepper half a revolution to open a flap for 10 seconds. |

## What we learned

- **Steppers were too slow.** At 5 RPM, a single sort took more than 10 seconds. BinSense switched to servos.
- **Substring matching was fragile.** `"Biodegradable"` also matches `"Non_Biodegradable"`, so the order of the `if` checks decided the result. BinSense uses an explicit class-to-bin mapping instead.
- **Opening a new serial connection on every detection reset the Arduino.** BinSense opens one connection at startup and keeps it.
- **There was no debouncing.** One item could trigger several sorts in a row. BinSense adds a confidence threshold and cooldowns on both the Python and Arduino sides.

This script imports from YOLOv5's `models/` and `utils/`. To run it, copy it into the `yolov5/` folder.
