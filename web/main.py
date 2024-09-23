from fasthtml.common import fast_app, Html, Head, Body, H1, Title, Div, P, serve
from google.cloud import storage
import json

app, rt = fast_app()

storage_client = storage.Client()

BUCKET_NAME = "aemet-yellow-watch"


@rt("/")
def get():
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob("swells.json")
        if blob is None:
            return Div(P("Blob not found"))

        else:
            data = blob.download_as_string()
            # convert to json_data
            json_data = json.loads(data)
            # display

            s = []
            swells_div = Div("there are swells")
            for swell in json_data:
                # print(swell)
                # print("hey[]")
                print(swell["startDate"])
                swell_div = Div(
                    P(f"Start Date: {swell['startDate']}"),
                    P(f"End Date: {swell['endDate']}"),
                )
                s.append(swell_div)
            page = Html(
                Head(Title("Swell Watch")),
                Body(H1("Swell Watch"), swells_div, *s),
            )
            return page
    except Exception as e:
        return Div(P(str(e)))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
