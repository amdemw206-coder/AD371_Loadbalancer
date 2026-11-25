import os
import socket
from fastapi import FastAPI

app = FastAPI()
INSTANCE_ID = os.getenv("INSTANCE_ID") or socket.gethostname()


@app.get("/")
def root():
    return {
        "message": "Response from private backend replica",
        "instance_id": INSTANCE_ID,
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok", "instance_id": INSTANCE_ID}