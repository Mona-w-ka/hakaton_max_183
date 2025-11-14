import threading
import requests
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from functools import lru_cache

app = FastAPI()

url_data = None
lock = threading.Lock()

class URLRequest(BaseModel):
    url: str

def background_updater():
    global url_data
    while True:
        try:
            response = requests.get("https://urlhaus.abuse.ch/downloads/text_online/", timeout=10)
            response.raise_for_status()
            urls = {
                line.strip()
                for line in response.text.splitlines()
                if line.strip() and not line.startswith('#')
            }
            with lock:
                url_data = urls
            check_url_cached.cache_clear()
        except Exception as e:
            print(f"Ошибка обновления данных: {e}")
        time.sleep(600)

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=background_updater, daemon=True)
    thread.start()

@lru_cache(maxsize=1000)
def check_url_cached(url: str) -> int:
    with lock:
        data_snapshot = url_data
    if data_snapshot is None:
        return 0
    return 1 if url in data_snapshot else 0

@app.post("/check")
def check(request: URLRequest):
    url = request.url.strip()
    print(url)
    if not url:
        raise HTTPException(status_code=300, detail="URL не указан")
    return {"result": check_url_cached(url)}