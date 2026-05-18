import os
import sys
from pathlib import Path

import django
from django.conf import settings
from django.db import connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_it.settings")

django.setup()

db = settings.DATABASES["default"]
print("database:", db["NAME"])
print("user:", db["USER"])
print("host:", db["HOST"])
print("port:", db["PORT"])

connection.ensure_connection()
print("connected")
