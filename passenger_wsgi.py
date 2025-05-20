# passenger_wsgi.py
import sys
sys.path.insert(0, "/home/mspinega/ondemand/dev/drone-image-processing-api")

from app import app as application  # must be named "application"