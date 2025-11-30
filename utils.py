import hashlib
import time
import base64
from datetime import datetime

#HELPER: IMAGE TO BASE64
def get_image_base64(path):
    """Converts an image file to a base64 string for HTML rendering"""
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except:
        return None

# UTILITY
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def now_ts() -> float:
    return time.time()

def human_time(ts: float) -> str:
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%Y-%m-%d %H:%M")
