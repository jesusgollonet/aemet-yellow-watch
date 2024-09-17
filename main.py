import requests
from bs4 import BeautifulSoup
from util import rgb_to_hsv, hsv_bounds, human_date, date_from_image

import cv2 as cv
import numpy as np

MIN_AREA = 700

# fetch and parse HTML content
response = requests.get(
    "https://www.aemet.es/es/eltiempo/prediccion/maritima?opc1=0&opc3=0&area=and2"
)
data = response.text
soup = BeautifulSoup(data, "html.parser")

images = soup.find_all("img", {"data-src": True})

# let's set up 2 alerts
"""
1. if there's swell bigger than MIN_AREA for at least 3 images in a row
2. if the swell touches our region

in both cases, swell direction
"""

swell_counter = 0
swell_detected = False

for image in images:
    try:
        response = requests.get(f"https://www.aemet.es/{image['data-src']}")
        response.raise_for_status()
        d = date_from_image(image)

        # Convert the response content to a NumPy array for OpenCV
        image_data = np.frombuffer(response.content, np.uint8)

        # Decode the image directly from the byte array
        img = cv.imdecode(image_data, cv.IMREAD_COLOR)
        img = img[22:500, 50:760]
        hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
        yellow = [255, 255, 110]
        lower, upper = hsv_bounds(rgb_to_hsv(yellow), 2)

        mask = cv.inRange(hsv, lower, upper)
        img = cv.bitwise_and(img, img, mask=mask)

        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        areas = [cv.contourArea(contour) for contour in contours]
        total_area = sum(areas)
        if total_area > MIN_AREA:
            swell_counter += 1
        else:
            swell_counter = 0

        if swell_counter >= 3 and not swell_detected:
            print(f"ALERT: Swell detected on {human_date(d)}")
            swell_detected = True

        if swell_detected and total_area < MIN_AREA:
            swell_detected = False
            print(f"ALERT: Swell ended on {human_date(d)}")

    except Exception as e:
        print(f"Error downloading image: {e}")
