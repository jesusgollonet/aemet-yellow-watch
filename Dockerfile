FROM python:3.12-slim

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
COPY main.py util.py ./
RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["python", "main.py"]
