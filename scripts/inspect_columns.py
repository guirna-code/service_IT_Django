import os
import sys
import django
from pathlib import Path


# Ensure project root is on sys.path so Django settings package can be imported
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
print('project_root:', project_root)
print('sys.path[0]:', sys.path[0])
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_it.settings')
try:
    django.setup()
except Exception as e:
    print('django.setup() error:', e)
    raise

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='app_utilisateur' ORDER BY ordinal_position")
    cols = [r[0] for r in cursor.fetchall()]

print('columns:', cols)
