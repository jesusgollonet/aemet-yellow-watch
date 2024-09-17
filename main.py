import requests
from bs4 import BeautifulSoup
from util import rgb_to_hsv, hsv_bounds, human_date, date_from_image

import cv2 as cv
import numpy as np

MIN_AREA = 700

response = requests.get(
    "https://www.aemet.es/es/eltiempo/prediccion/maritima?opc1=0&opc3=0&area=and2"
)
data = response.text
soup = BeautifulSoup(data, "html.parser")


# Get all images with data-src attribute
images = soup.find_all("img", {"data-src": True})


for image in images:
    # Download image
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
            cv.putText(
                img,
                str(human_date(d) + ": " + str(total_area)),
                (10, 30),
                cv.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )
            # area = cv.contourArea(contours[0])
            # Run your color detection or any OpenCV operation on `img`
            cv.imshow("Image", img)

            # Wait for a key press
            key = cv.waitKey(0)

            # If 'q' is pressed, break the loop and exit the program
            if key == ord("q"):
                print("Exiting the program.")
                break
            cv.destroyAllWindows()
    except Exception as e:
        print(f"Error downloading image: {e}")

    with open(f"images/{image['data-src'].split('/')[-1]}", "wb") as file:
        file.write(response.content)
