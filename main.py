import requests
import os
from bs4 import BeautifulSoup

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
    except Exception as e:
        print(f"Error downloading image: {e}")

    with open(f"images/{image['data-src'].split('/')[-1]}", "wb") as file:
        file.write(response.content)
