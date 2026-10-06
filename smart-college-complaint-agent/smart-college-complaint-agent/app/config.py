import os
import json
import time
import urllib.request
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOADS_DIR = BASE_DIR / "uploads"

# Ensure data and uploads directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Default Student Credentials
STUDENT_USERNAME = os.getenv("STUDENT_USERNAME", "VCET26")
STUDENT_PASSWORD = os.getenv("STUDENT_PASSWORD", "velalar")

# Data Store File Paths
COMPLAINTS_FILE = DATA_DIR / "complaints.json"
DEPARTMENTS_FILE = DATA_DIR / "departments.json"
STAFF_FILE = DATA_DIR / "staff.json"
HISTORY_FILE = DATA_DIR / "complaint_history.json"
INCIDENTS_FILE = DATA_DIR / "incidents.json"
NOTIFICATIONS_FILE = DATA_DIR / "notifications.json"

# AI Agent Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:latest")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# SLA Configuration
SLA_PENDING_HOURS = int(os.getenv("SLA_PENDING_HOURS", "24"))

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# In-memory TTL cache for Ollama probe
_ollama_cache = {}


def is_ollama_available(model_name: str = OLLAMA_MODEL, host_url: str = OLLAMA_BASE_URL, timeout: float = 0.2) -> bool:
    """
    Check if Ollama server is running AND the requested model is downloaded locally.
    Uses 15-second in-memory TTL caching to avoid repetitive network overhead.
    """
    cache_key = (model_name, host_url)
    now = time.time()
    if cache_key in _ollama_cache:
        cached_val, timestamp = _ollama_cache[cache_key]
        if now - timestamp < 15.0:
            return cached_val

    result = False
    try:
        url = f"{host_url.rstrip('/')}/api/tags"
        req = urllib.request.Request(url, headers={"User-Agent": "SmartCollegeAgent"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                base_name = model_name.split(":")[0]
                result = any(model_name in m or m.startswith(base_name) for m in models)
    except Exception:
        result = False

    _ollama_cache[cache_key] = (result, now)
    return result
