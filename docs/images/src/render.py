# Render every image in this folder to docs/images/*.png at 2x for sharpness.
#
#   pip install playwright && playwright install chromium
#   python docs/images/src/render.py
from pathlib import Path

from playwright.sync_api import sync_playwright

SRC = Path(__file__).resolve().parent
OUT = SRC.parent
SIZES = {
    "cover": (1280, 640),
    "cover-linkedin": (1200, 627),
    **{f"gallery-{i}": (1600, 1000) for i in range(1, 6)},
}

with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, (w, h) in SIZES.items():
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        page.goto((SRC / f"{name}.html").as_uri())
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=OUT / f"{name}.png")
        page.close()
        print(f"{name}.png  {w}x{h} @2x")
    browser.close()
