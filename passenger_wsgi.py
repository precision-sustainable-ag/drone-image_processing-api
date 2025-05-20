import sys
import os

# Path to your virtual environment's site-packages
venv_site_packages = "/home/mspinega/ondemand/dev/drone-image_processing-api/venv/lib/python3.9/site-packages"

# Add venv site-packages to sys.path
sys.path.insert(0, venv_site_packages)

# Add your app path
sys.path.insert(0, "/home/mspinega/ondemand/dev/drone-image_processing-api")

# Import the Flask app
from app import app as application  # must be named 'application'