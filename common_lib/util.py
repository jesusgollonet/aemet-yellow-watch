import cv2 as cv
import numpy as np
from datetime import datetime, timedelta
import humanize


def draw_text(text, img):
    cv.putText(
        img,
        str(text),
        (10, 30),
        cv.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )


def rgb_to_hsv(rgb: list) -> np.ndarray:
    source = np.array(rgb, dtype=np.uint8).reshape(1, 1, 3)
    return cv.cvtColor(source, cv.COLOR_RGB2HSV)


def hsv_bounds(hsv: np.ndarray, margin: int = 2) -> tuple:
    h = hsv[0, 0, 0]
    return (np.array([h - margin, 100, 100]), np.array([h + margin, 255, 255]))


def detect_yellow():
    return None

def color_contours(img, color_rgb):
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    lower, upper = hsv_bounds(rgb_to_hsv(color_rgb), 10)
    mask = cv.inRange(hsv, lower, upper)
    img = cv.bitwise_and(img, img, mask=mask)
    contours, _ = cv.findContours(
        mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
    )
    return contours


def date_from_image(image):
    date_source = image["data-src"].split("/")[-1].split("_")[0]
    base_date_str, offset = date_source.split("+")
    base_date = datetime.strptime(base_date_str, "%Y%m%d%H")
    date = base_date + timedelta(hours=int(offset))
    return date


def human_date(date):
    return humanize.naturaltime(date)
