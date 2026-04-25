from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
import requests
import traceback
from datetime import datetime
import os

AGENT_URL = os.getenv("AGENT_URL")

app = FastAPI()

# 🔹 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🧠 Send structured log
def send_log(data: dict):
    if not AGENT_URL:
        print("❌ AGENT_URL not set")
        return

    try:
        print("📡 Sending request to:", AGENT_URL)

        res = requests.post(AGENT_URL, json=data, timeout=10)

        print("✅ Agent responded!")
        print("Status:", res.status_code)
        print("Body:", res.text)

    except Exception as e:
        print("❌ Log send failed:", e)


# 🔥 MIDDLEWARE (FIXED)
@app.middleware("http")
async def log_errors(request: Request, call_next):
    try:
        response = await call_next(request)

        if response.status_code >= 400:
            log_data = {
                "message": f"HTTP {response.status_code} error",
                "error_type": "HTTPError",
                "endpoint": request.url.path,
                "method": request.method,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "todo-backend"
            }

            print("🔥 HTTP error detected")
            send_log(log_data)

        return response

    except Exception as e:
        log_data = {
            "message": f"{type(e).__name__}: {str(e)}",
            "error_type": type(e).__name__,
            "endpoint": request.url.path,
            "method": request.method,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "todo-backend",
            "stack_trace": traceback.format_exc()
        }

        print("🔥 Runtime exception detected")
        send_log(log_data)

        raise e


# 🟢 Normal route
@app.get("/")
def home():
    return {"message": "Backend running"}


# 🔴 Runtime error
@app.get("/crash")
def crash():
    x = 10 / 0
    return {"result": x}


# 🔴 HTTP error
@app.get("/item/{id}")
def get_item(id: int):
    if id > 5:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": id}


# 🔴 Index error
@app.get("/index-error")
def index_error():
    arr = [1, 2, 3]
    return arr[10]


# 🔥 FIXED TODOS ROUTE
@app.post("/todos")
async def add_todo(data: dict = Body(...)):

    title = data.get("title", "")

    print("📥 Received todo:", title)

    # 🔥 DB Errors
    if title == "db_fail":
        raise Exception("DatabaseConnectionError: could not connect to PostgreSQL")

    if title == "duplicate":
        raise Exception("IntegrityError: duplicate key value violates unique constraint")

    if title == "timeout":
        raise Exception("DatabaseTimeoutError: query execution exceeded time limit")

    # 🔥 Validation Error
    if len(title) > 20:
        raise ValueError("ValidationError: title too long")

    # 🔥 Type Error
    if title == "type":
        x = "string" + 10

    # 🔥 Key Error
    if title == "key":
        obj = {"name": "todo"}
        return obj["missing"]

    # 🔥 External API failure
    if title == "api":
        requests.get("https://invalid-api.example.com", timeout=1)

    return {"status": "todo added"}
