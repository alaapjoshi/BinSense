# yolov5/ (vendored)

This folder is a copy of [Ultralytics YOLOv5](https://github.com/ultralytics/yolov5), licensed under [AGPL-3.0](LICENSE). It's included so that BinSense runs without extra setup.

The BinSense-specific files are:

| File | Purpose |
|---|---|
| `binsense.py` | The main BinSense app: webcam detection, the recycle/trash decision, the HUD, and Arduino serial output |
| `best.pt` | YOLOv5 weights fine-tuned on 19 household-waste classes |
| `requirements.txt` | Upstream requirements, plus `pyserial` |

Everything else is upstream YOLOv5 code (models, utils, and training and validation scripts). See the [main README](../README.md) for setup and usage.
