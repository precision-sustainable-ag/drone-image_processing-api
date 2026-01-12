# passenger_wsgi.py (backend)
import os, sys, glob

BASE = "/usr/local/usrapps/drones/drone-data-viewer/drone-image_processing-api"
VENV = os.path.join(BASE, ".venv")
candidates = glob.glob(os.path.join(VENV, "lib", "python*", "site-packages"))
if candidates and candidates[0] not in sys.path:
    sys.path.insert(0, candidates[0])
if BASE not in sys.path:
    sys.path.insert(0, BASE)

os.environ["VIRTUAL_ENV"] = VENV
os.environ["PATH"] = os.path.join(VENV, "bin") + ":" + os.environ.get("PATH","")
os.environ["ENVIRONMENT"] = "prod"

# ✅ writeable locations in HOME for OOD
HOME = os.path.expanduser("~")
os.environ.setdefault("APP_LOG_DIR", os.path.join(HOME, "ondemand", "data", "backend", "logs"))
os.environ.setdefault("APP_STORAGE_DIR", os.path.join(HOME, "ondemand", "data", "backend", "storage"))

# ensure they exist
os.makedirs(os.environ["APP_LOG_DIR"], exist_ok=True)
os.makedirs(os.environ["APP_STORAGE_DIR"], exist_ok=True)

from app import app as application
