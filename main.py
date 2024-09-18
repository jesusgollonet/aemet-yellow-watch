from swell_detector import detect_swells, Swell

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def run_script() -> list[Swell]:
    return detect_swells()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
