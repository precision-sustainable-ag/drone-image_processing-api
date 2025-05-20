import sys
import os

# Activate your virtual environment
venv_path = "/home/mspinega/ondemand/dev/drone-image_processing-api/venv"
activate_this = os.path.join(venv_path, "bin", "activate_this.py")
exec(open(activate_this).read(), dict(__file__=activate_this))

# Add your app to the path
sys.path.insert(0, "/home/mspinega/ondemand/dev/drone-image_processing-api")

from app import app as application  # must be named "application"
