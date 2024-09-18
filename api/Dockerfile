FROM python:3.12-slim


WORKDIR /app

COPY requirements.txt requirements.txt
COPY main.py ./
RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["python", "main.py"]
