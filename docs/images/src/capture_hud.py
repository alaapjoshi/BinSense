# Capture the real BinSense HUD without an Arduino attached.
# Runs vision/binsense.py unmodified, swapping the serial port for a stub and saving
# the OpenCV window to a PNG instead of showing it. The input image is fed twice, with
# the clock moved forward 2 s between frames, so the saved frame shows the HUD after
# the sort flash has faded.
#
#   python docs/images/src/capture_hud.py vision docs/images/photo-detection.jpg docs/images/src/hud-capture.png
import os
import shutil
import sys
import tempfile
import time

import cv2
import serial

vision, image, out = (os.path.abspath(p) for p in sys.argv[1:4])
sys.path.insert(0, vision)
os.chdir(vision)

src = tempfile.mkdtemp()
for name in ("frame1.jpg", "frame2.jpg"):
    shutil.copy(image, os.path.join(src, name))

clock = {"offset": 0.0}
_real_time = time.time
time.time = lambda: _real_time() + clock["offset"]


def save_frame(name, img):
    cv2.imwrite(out, img)
    clock["offset"] += 2.0

sent = []


class FakeArduino:
    def __init__(self, *args, **kwargs):
        pass

    def write(self, data):
        sent.append(data)

    def flush(self):
        pass


serial.Serial = FakeArduino
time.sleep = lambda s: None
cv2.imshow = save_frame
cv2.waitKey = lambda *args: 1

import binsense  # noqa: E402

binsense.run(source=src, conf_thres=0.35, device="cpu", port="stub")
print("sent to Arduino:", sent, "|", binsense.last_action_text)
