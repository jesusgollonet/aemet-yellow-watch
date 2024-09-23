import streamlink as sl
import cv2 as cv
from datetime import datetime
import tempfile
from google.cloud import storage


def upload_blob(bucket_name, local_filename, destination_blob_name):
    print("upload blob")
    """Uploads a file to the bucket."""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(local_filename)
    print(f"File {destination_blob_name} uploaded to {bucket_name}.")


def capture_frame(m3u8_url, stream_name):
    session = sl.Streamlink(options={"http-headers": "Referer=https://meteo365.es/"})
    streams = session.streams(m3u8_url)
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file_name = temp_file.name

    fd = streams["best"].open()
    c = 0
    while True and c < 200:
        chunk = fd.read(1024)
        if not chunk:
            break
        temp_file.write(chunk)
        c += 1
    fd.close()
    temp_file.close()
    cap = cv.VideoCapture(temp_file_name)
    _, frame = cap.read()
    print(f"storing image in {stream_name}...")
    file_name = f"{stream_name}_{datetime.timestamp(datetime.now()) }.jpg"
    print("filenmae", file_name)
    cv.imwrite(f"frames/{file_name}", frame)
    print(file_name, stream_name)
    upload_blob(
        "aemet-yellow-watch",
        f"frames/{file_name}",
        f"frames/{file_name}",
    )
    cap.release()


if __name__ == "__main__":
    print("scirpt!")
    capture_frame("https://livecams.meteo365.es/hls_live/nerjaplaya.m3u8", "meteo365")
