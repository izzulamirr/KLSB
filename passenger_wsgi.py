import os, sys

PROJECT_ROOT = os.path.dirname(__file__)
# if you created a virtualenv inside the project named 'venv', ensure it is used
VENV_BIN = os.path.join(PROJECT_ROOT, "venv", "bin")
os.environ['PATH'] = VENV_BIN + os.pathsep + os.environ.get('PATH', '')

sys.path.insert(0, PROJECT_ROOT)
from app import create_app

# Passenger expects the WSGI callable to be `application`
application = create_app()




