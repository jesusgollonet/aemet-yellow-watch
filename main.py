import requests
import os
from bs4 import BeautifulSoup

import cv2 as cv
import numpy as np

response = requests.get(
    "https://www.aemet.es/es/eltiempo/prediccion/maritima?opc1=0&opc3=0&area=and2"
)
data = response.text
soup = BeautifulSoup(data, "html.parser")
os.makedirs("images", exist_ok=True)

# Get all images with data-src attribute
images = soup.find_all("img", {"data-src": True})
for image in images:
    # Download image
    try:
        response = requests.get(f"https://www.aemet.es/{image['data-src']}")
        response.raise_for_status()

        # Convert the response content to a NumPy array for OpenCV
        image_data = np.frombuffer(response.content, np.uint8)

        # Decode the image directly from the byte array
        img = cv.imdecode(image_data, cv.IMREAD_COLOR)
        img = img[22:500, 50:760]

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
