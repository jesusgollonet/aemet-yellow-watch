"""
Tracer bullet: detect whether a yellow swell area touches a given coastline region.

Usage:
    python coastline_touch.py [image_path]

If no image is provided, downloads the latest AEMET forecast image.
"""

import sys
import cv2 as cv
import numpy as np
import requests
from bs4 import BeautifulSoup

# ── colour constants ──────────────────────────────────────────────────────────
YELLOW_RGB = (255, 255, 110)   # AEMET yellow swell warning
LAND_RGB   = (255, 227, 173)   # beige land mass

# image crop applied by the existing worker (removes map title / legend)
CROP = np.s_[22:500, 50:760]

# "small area of coastline" we care about — Málaga coast, in cropped-image pixels
# Adjust this box to monitor a different stretch of coast.
MALAGA_ROI = (430, 270, 80, 60)  # (x, y, width, height)

# proximity threshold in pixels: swell is considered touching if it comes
# within this many pixels of a land contour point
TOUCH_THRESHOLD = 6


# ── helpers ───────────────────────────────────────────────────────────────────
def _hsv_bounds(rgb: tuple, h_delta=5, s_delta=30, v_delta=30):
    source = np.array(rgb, dtype=np.uint8).reshape(1, 1, 3)
    hsv = cv.cvtColor(source, cv.COLOR_RGB2HSV)
    h, s, v = hsv[0, 0].astype(np.int16)
    lo = np.array([max(h - h_delta, 0),   max(s - s_delta, 0),   max(v - v_delta, 0)],   dtype=np.uint8)
    hi = np.array([min(h + h_delta, 179), min(s + s_delta, 255), min(v + v_delta, 255)], dtype=np.uint8)
    return lo, hi


def _contours_for_color(img_bgr: np.ndarray, rgb: tuple) -> list:
    hsv = cv.cvtColor(img_bgr, cv.COLOR_BGR2HSV)
    lo, hi = _hsv_bounds(rgb)
    mask = cv.inRange(hsv, lo, hi)
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    return list(contours)


def _roi_rect(roi):
    """Return (x1, y1, x2, y2) from (x, y, w, h)."""
    x, y, w, h = roi
    return x, y, x + w, y + h


# ── core function ─────────────────────────────────────────────────────────────
def touches_coast(img_bgr: np.ndarray, roi: tuple) -> dict:
    """
    Determine whether yellow swell touches the coastline inside `roi`.

    Parameters
    ----------
    img_bgr : np.ndarray
        Full (cropped) AEMET forecast image in BGR.
    roi : tuple
        (x, y, width, height) in image pixels — the coastline segment to watch.

    Returns
    -------
    dict with keys:
        touching      : bool
        touch_points  : list of (x, y) pixel coordinates
        swell_area    : total yellow area in the full image (px²)
    """
    x1, y1, x2, y2 = _roi_rect(roi)

    swell_contours = _contours_for_color(img_bgr, YELLOW_RGB)
    land_contours  = _contours_for_color(img_bgr, LAND_RGB)

    # keep only land contour points that fall inside the ROI
    roi_land_points = []
    for contour in land_contours:
        for pt in contour:
            px, py = int(pt[0][0]), int(pt[0][1])
            if x1 <= px <= x2 and y1 <= py <= y2:
                roi_land_points.append((px, py))

    # check each ROI land point against every swell contour
    touch_points = []
    for p in roi_land_points:
        for sc in swell_contours:
            dist = cv.pointPolygonTest(sc, p, measureDist=True)
            if -TOUCH_THRESHOLD <= dist < TOUCH_THRESHOLD:
                touch_points.append(p)
                break  # one swell contour is enough

    swell_area = sum(
        cv.contourArea(c) for c in swell_contours
    )

    return {
        "touching":     len(touch_points) > 0,
        "touch_points": touch_points,
        "swell_area":   swell_area,
    }


def annotate(img_bgr: np.ndarray, result: dict, roi: tuple) -> np.ndarray:
    """Draw ROI box and touch points on a copy of the image."""
    out = img_bgr.copy()
    x, y, w, h = roi
    colour = (0, 0, 255) if result["touching"] else (0, 255, 0)
    cv.rectangle(out, (x, y), (x + w, y + h), colour, 2)
    for pt in result["touch_points"]:
        cv.circle(out, pt, 5, (0, 0, 255), -1)
    label = "TOUCHING" if result["touching"] else "clear"
    cv.putText(out, label, (x, y - 6), cv.FONT_HERSHEY_SIMPLEX, 0.6, colour, 2)
    return out


# ── image loading ─────────────────────────────────────────────────────────────
def load_from_file(path: str) -> np.ndarray:
    img = cv.imread(path, cv.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return img[CROP]


def fetch_latest_aemet() -> np.ndarray:
    resp = requests.get(
        "https://www.aemet.es/es/eltiempo/prediccion/maritima?opc1=0&opc3=0&area=and2",
        timeout=10,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    images = soup.find_all("img", {"data-src": True})
    if not images:
        raise RuntimeError("No forecast images found on AEMET page")

    # use the first (most current) image
    img_url = f"https://www.aemet.es/{images[0]['data-src']}"
    img_resp = requests.get(img_url, timeout=10)
    img_resp.raise_for_status()

    arr = np.frombuffer(img_resp.content, np.uint8)
    img = cv.imdecode(arr, cv.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"Could not decode image from {img_url}")
    return img[CROP]


# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        img = load_from_file(sys.argv[1])
        print(f"Loaded image from {sys.argv[1]}")
    else:
        print("No image path given — fetching latest AEMET forecast…")
        img = fetch_latest_aemet()
        print("Fetched.")

    result = touches_coast(img, MALAGA_ROI)

    print(f"\nROI          : {MALAGA_ROI}  (Málaga coast)")
    print(f"Yellow area  : {result['swell_area']:.0f} px²")
    print(f"Touch points : {len(result['touch_points'])}")
    print(f"Touching     : {result['touching']}")

    out = annotate(img, result, MALAGA_ROI)
    out_path = "/tmp/coastline_touch_result.png"
    cv.imwrite(out_path, out)
    print(f"\nAnnotated image saved to {out_path}")
