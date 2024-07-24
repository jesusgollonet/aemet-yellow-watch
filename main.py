import requests
from bs4 import BeautifulSoup

response = requests.get(
    "https://www.aemet.es/es/eltiempo/prediccion/maritima?opc1=0&opc3=0&area=and2"
)
data = response.text
soup = BeautifulSoup(data, "html.parser")

# Get all images with data-src attribute
images = soup.find_all("img", {"data-src": True})
for image in images:
    try:
        print(image["data-src"])
        # Download image
        response = requests.get(f"https://www.aemet.es/{image["data-src"]}" )
        with open(f"images/{image['data-src'].split('/')[-1]}", "wb") as file:
            file.write(response.content)
    except KeyError:
        print("No src attribute")
