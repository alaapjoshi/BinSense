# =========================
# YOLOv5 + Arduino Smart Bin
# =========================

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch
import cv2
import serial

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from models.common import DetectMultiBackend
from utils.dataloaders import LoadStreams, LoadImages
from utils.general import check_img_size, non_max_suppression, scale_boxes
from utils.torch_utils import select_device, smart_inference_mode
from ultralytics.utils.plotting import Annotator, colors

# =========================
# CONFIG
# =========================

recycling_items = {
     "egg shell", "fruit peels",
    "glass bottle", "paper", "pet bottle", "plastic bottle",
    "plastic container", "uht carton", "vegetable peels", "treeleaves"
}

non_recycling_items = {
    "facemask", "food wrapper", "left-over food",
    "plastic bag", "plastic sachet", "plastic straw",
    "styrofoam containers", "aluminum"
}

class_conf_overrides = {
    "paper - Biodegradable-Recyclable": 1.1,
    "vegetable peels - Biodegradable": 1.1,
    "fruit peels - Biodegradable": 1.1,
    "styrofoam containers - Non_Biodegradable": 1.1,
    "left-over food - Biodegradable": 1.1,
    "cardboard": 1.1,
    "uht carton": 1.1,
    "aluminum": 1.1,
    "aluminum - Non_biodegradable-Recyclable": 1.1,
    "cardboard - Non_Biodegradable-Recyclable": 1.1,
    "uht carton - Non_Biodegradable-Recyclable": 1.1,

}

COOLDOWN = 3.0        # seconds between Arduino signals
FLASH_DURATION = 0.7  # seconds for the screen flash

# Arduino serial port (override with --port)
DEFAULT_PORT = "/dev/cu.usbserial-2120"

# Stats
recycled_count   = 0
trash_count      = 0
last_action_text = ""
last_sent_time   = 0

# Flash state
flash_timer = 0
flash_type  = None  # "recycle" or "trash"

# =========================
# COLORS  (BGR)
# =========================
C_GREEN    = (0, 210, 90)
C_RED      = (40, 40, 220)
C_WHITE    = (240, 240, 240)
C_DIM      = (100, 105, 115)
C_PANEL    = (18, 20, 26)
C_ACCENT_G = (0, 255, 120)
C_ACCENT_R = (50, 50, 255)
C_BORDER   = (45, 50, 62)

# =========================
# DRAW HELPERS
# =========================

def draw_rounded_rect_fill(img, x1, y1, x2, y2, color, alpha=0.35, radius=12):
    overlay = img.copy()
    r = radius
    cv2.rectangle(overlay, (x1 + r, y1), (x2 - r, y2), color, -1)
    cv2.rectangle(overlay, (x1, y1 + r), (x2, y2 - r), color, -1)
    for cx, cy in [(x1+r, y1+r), (x2-r, y1+r), (x1+r, y2-r), (x2-r, y2-r)]:
        cv2.circle(overlay, (cx, cy), r, color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


def draw_rounded_rect_border(img, x1, y1, x2, y2, color, thickness=2, radius=12):
    r = radius
    cv2.line(img, (x1+r, y1), (x2-r, y1), color, thickness)
    cv2.line(img, (x1+r, y2), (x2-r, y2), color, thickness)
    cv2.line(img, (x1, y1+r), (x1, y2-r), color, thickness)
    cv2.line(img, (x2, y1+r), (x2, y2-r), color, thickness)
    cv2.ellipse(img, (x1+r, y1+r), (r,r), 180, 0, 90, color, thickness)
    cv2.ellipse(img, (x2-r, y1+r), (r,r), 270, 0, 90, color, thickness)
    cv2.ellipse(img, (x1+r, y2-r), (r,r),  90, 0, 90, color, thickness)
    cv2.ellipse(img, (x2-r, y2-r), (r,r),   0, 0, 90, color, thickness)


def draw_corner_brackets(img, x1, y1, x2, y2, color, size=24, thickness=2):
    for ox, oy, dx, dy in [(x1,y1,1,1),(x2,y1,-1,1),(x1,y2,1,-1),(x2,y2,-1,-1)]:
        cv2.line(img, (ox, oy), (ox + dx*size, oy), color, thickness)
        cv2.line(img, (ox, oy), (ox, oy + dy*size), color, thickness)


def draw_scanlines(img, step=4):
    h, w = img.shape[:2]
    for y in range(0, h, step):
        cv2.line(img, (0, y), (w, y), (0, 0, 0), 1)


def centered_text(img, text, font, scale, color, thickness, x1, x2, y):
    sz = cv2.getTextSize(text, font, scale, thickness)[0]
    tx = x1 + ((x2 - x1) - sz[0]) // 2
    cv2.putText(img, text, (tx, y), font, scale, color, thickness)

# =========================
# MAIN HUD DRAW
# =========================

FONT = cv2.FONT_HERSHEY_DUPLEX

def draw_hud(im0, recycled_count, trash_count, last_action_text,
             flash_timer, flash_type, now, detected_label=None, detected_conf=None):

    h, w = im0.shape[:2]
    panel_w = 240

    # ── SCREEN FLASH ─────────────────────────────────────────────────
    if flash_timer > 0:
        elapsed  = now - flash_timer
        progress = elapsed / FLASH_DURATION
        if progress < 1.0:
            intensity = 0.50 * (1.0 - progress)
            if flash_type == "recycle":
                flash_bgr = (0, int(200 * intensity), int(70 * intensity))
                glow_bgr  = C_ACCENT_G
            else:
                flash_bgr = (0, 0, int(230 * intensity))
                glow_bgr  = C_ACCENT_R

            overlay = im0.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), flash_bgr, -1)
            cv2.addWeighted(overlay, intensity, im0, 1 - intensity, 0, im0)

            glow_h = max(1, int(14 * (1.0 - progress)))
            cv2.rectangle(im0, (0, 0), (w, glow_h), glow_bgr, -1)
            cv2.rectangle(im0, (0, h - glow_h), (w, h), glow_bgr, -1)

    # ── SIDEBAR BACKGROUND ────────────────────────────────────────────
    overlay = im0.copy()
    cv2.rectangle(overlay, (0, 0), (panel_w, h), C_PANEL, -1)
    cv2.addWeighted(overlay, 0.88, im0, 0.12, 0, im0)
    cv2.line(im0, (panel_w, 0), (panel_w, h), C_BORDER, 2)

    px = 16  # left padding inside panel

    # ── TITLE ─────────────────────────────────────────────────────────
    cv2.putText(im0, "BIN", (px, 50), FONT, 1.7, C_ACCENT_G, 3)
    cv2.putText(im0, "SENSE", (px, 82), FONT, 1.0, C_WHITE, 2)
    cv2.line(im0, (px, 96), (panel_w - px, 96), C_BORDER, 1)

    # ── LIVE PULSE DOT ────────────────────────────────────────────────
    pulse = int(160 + 95 * abs(np.sin(now * 2.8)))
    cv2.circle(im0, (panel_w - 20, 20), 6, (0, pulse, 0), -1)
    cv2.putText(im0, "LIVE", (panel_w - 58, 25), FONT, 0.4, (0, pulse, 0), 1)

    # ── RECYCLED BLOCK ────────────────────────────────────────────────
    r_on = flash_type == "recycle" and flash_timer > 0 and (now - flash_timer) < FLASH_DURATION
    r_col = C_ACCENT_G if r_on else C_GREEN

    draw_rounded_rect_fill(im0, px - 4, 106, panel_w - px + 4, 240,
                           (0, 160, 60) if r_on else (0, 50, 25), alpha=0.3)
    draw_rounded_rect_border(im0, px - 4, 106, panel_w - px + 4, 240, r_col, radius=8)

    cv2.putText(im0, "RECYCLED", (px + 4, 130), FONT, 0.58, r_col, 1)
    centered_text(im0, str(recycled_count), FONT, 3.2, r_col, 6,
                  px, panel_w - px, 218)

    # ── TRASH BLOCK ───────────────────────────────────────────────────
    t_on = flash_type == "trash" and flash_timer > 0 and (now - flash_timer) < FLASH_DURATION
    t_col = C_ACCENT_R if t_on else C_RED

    draw_rounded_rect_fill(im0, px - 4, 252, panel_w - px + 4, 386,
                           (0, 0, 140) if t_on else (30, 0, 40), alpha=0.3)
    draw_rounded_rect_border(im0, px - 4, 252, panel_w - px + 4, 386, t_col, radius=8)

    cv2.putText(im0, "TRASH", (px + 4, 276), FONT, 0.58, t_col, 1)
    centered_text(im0, str(trash_count), FONT, 3.2, t_col, 6,
                  px, panel_w - px, 364)

    # ── RECYCLE RATE BAR ──────────────────────────────────────────────
    total = recycled_count + trash_count
    rate  = int((recycled_count / total) * 100) if total > 0 else 0

    cv2.line(im0, (px, 398), (panel_w - px, 398), C_BORDER, 1)
    cv2.putText(im0, "RECYCLE RATE", (px, 420), FONT, 0.48, C_DIM, 1)
    cv2.putText(im0, f"{rate}%", (px, 452), FONT, 1.5, C_WHITE, 2)

    bar_y = 462
    bar_w = panel_w - px * 2
    cv2.rectangle(im0, (px, bar_y), (px + bar_w, bar_y + 8), C_BORDER, -1)
    if rate > 0:
        cv2.rectangle(im0, (px, bar_y), (px + int(bar_w * rate / 100), bar_y + 8), C_ACCENT_G, -1)

    # ── DETECTION READOUT ─────────────────────────────────────────────
    cv2.line(im0, (px, h - 120), (panel_w - px, h - 120), C_BORDER, 1)
    cv2.putText(im0, "DETECTING", (px, h - 100), FONT, 0.46, C_DIM, 1)

    if detected_label and detected_conf is not None:
        short = (detected_label[:14] + "..") if len(detected_label) > 14 else detected_label
        cv2.putText(im0, short.upper(), (px, h - 68), FONT, 0.62, C_WHITE, 1)
        conf_col = C_ACCENT_G if detected_label in recycling_items else C_ACCENT_R
        cv2.putText(im0, f"{detected_conf*100:.1f}%", (px, h - 36), FONT, 1.2, conf_col, 2)
    else:
        cv2.putText(im0, "---", (px, h - 68), FONT, 0.62, C_DIM, 1)

    # ── LAST ACTION BANNER ────────────────────────────────────────────
    if last_action_text:
        is_rec  = "Recycled" in last_action_text
        b_color = C_ACCENT_G if is_rec else C_ACCENT_R
        text_up = last_action_text.upper()

        sz  = cv2.getTextSize(text_up, FONT, 1.3, 3)[0]
        tx  = panel_w + ((w - panel_w) - sz[0]) // 2
        ty  = h - 24

        draw_rounded_rect_fill(im0,
                               tx - 20, ty - sz[1] - 12,
                               tx + sz[0] + 20, ty + 12,
                               b_color, alpha=0.45, radius=10)
        draw_rounded_rect_border(im0,
                                 tx - 20, ty - sz[1] - 12,
                                 tx + sz[0] + 20, ty + 12,
                                 b_color, thickness=2, radius=10)
        cv2.putText(im0, text_up, (tx, ty), FONT, 1.3, C_WHITE, 3)

    # ── VIEWPORT CORNER BRACKETS ──────────────────────────────────────
    m = 10
    now_flash = flash_timer > 0 and (now - flash_timer) < FLASH_DURATION
    brk_col = C_ACCENT_G if (now_flash and flash_type == "recycle") \
         else C_ACCENT_R if (now_flash and flash_type == "trash") \
         else C_BORDER
    draw_corner_brackets(im0, panel_w + m, m, w - m, h - m, brk_col, size=30, thickness=2)

    # ── SCANLINES ─────────────────────────────────────────────────────
    draw_scanlines(im0, step=4)

    return im0


# =========================
# MAIN DETECTION FUNCTION
# =========================

@smart_inference_mode()
def run(
    weights=ROOT / "best.pt",
    source="0",
    imgsz=(640, 640),
    conf_thres=0.25,
    iou_thres=0.45,
    max_det=1000,
    device="",
    port=DEFAULT_PORT
):
    global recycled_count, trash_count, last_action_text, last_sent_time
    global flash_timer, flash_type

    arduino = serial.Serial(port, 9600, timeout=2)
    time.sleep(2)  # Arduino resets when the port opens

    source = str(source)
    device = select_device(device)
    model  = DetectMultiBackend(weights, device=device)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz  = check_img_size(imgsz, s=stride)

    webcam = source.isnumeric()
    if webcam:
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt)

    model.warmup(imgsz=(1, 3, *imgsz))

    for path, im, im0s, vid_cap, s in dataset:

        im = torch.from_numpy(im).to(model.device)
        im = im.float() / 255.0
        if len(im.shape) == 3:
            im = im[None]

        pred = model(im)
        pred = non_max_suppression(pred, conf_thres, iou_thres)

        for i, det in enumerate(pred):

            im0 = im0s[i].copy() if webcam else im0s.copy()
            annotator = Annotator(im0, line_width=2)

            detected_label = None
            detected_conf  = None

            if len(det):
                det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()
                det = det[det[:, 4].argsort(descending=True)]
                best = det[0]

                *xyxy, conf, cls = best
                c          = int(cls)
                label_name = names[c]
                base_name  = label_name.split(" - ")[0].strip().lower()
                min_conf   = class_conf_overrides.get(label_name, conf_thres)

                if conf >= min_conf:
                    detected_label = base_name
                    detected_conf  = float(conf)
                    now = time.time()
                    print(base_name)

                    if conf >= 0.70 and (now - last_sent_time) >= COOLDOWN:
                        if base_name in recycling_items:
                            arduino.write(b"1\n")
                            arduino.flush()
                            last_sent_time   = now
                            recycled_count  += 1
                            last_action_text = f"Recycled!  {base_name}"
                            flash_timer      = now
                            flash_type       = "recycle"
                        elif base_name in non_recycling_items:
                            arduino.write(b"0\n")
                            arduino.flush()
                            last_sent_time   = now
                            trash_count     += 1
                            last_action_text = f"Trashed!  {base_name}"
                            flash_timer      = now
                            flash_type       = "trash"

                    box_col = C_ACCENT_G if base_name in recycling_items else C_ACCENT_R
                    annotator.box_label(xyxy, f"{base_name}  {conf*100:.1f}%", color=box_col)

            # Draw frame + HUD
            im0 = annotator.result()
            im0 = draw_hud(im0, recycled_count, trash_count, last_action_text,
                           flash_timer, flash_type, time.time(),
                           detected_label, detected_conf)

            cv2.imshow("BinSense", im0)
            cv2.waitKey(1)


# =========================
# CLI
# =========================

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights",    type=str,   default=ROOT / "best.pt")
    parser.add_argument("--source",     type=str,   default="0")
    parser.add_argument("--imgsz",      nargs="+",  type=int, default=[640])
    parser.add_argument("--conf-thres", type=float, default=0.35)
    parser.add_argument("--iou-thres",  type=float, default=0.45)
    parser.add_argument("--device",     default="")
    parser.add_argument("--port",       type=str,   default=DEFAULT_PORT)
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1
    return opt

def main(opt):
    run(**vars(opt))

if __name__ == "__main__":
    opt = parse_opt()
    main(opt)
