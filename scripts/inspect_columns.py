import os
import sys
from pathlib import Path

import django
from django.db import connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_it.settings")

django.setup()

tables = [
    "app_utilisateur",
    "app_machine",
    "app_composant",
    "app_rapportintervention",
]

with connection.cursor() as cursor:
    for table in tables:
        cursor.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
            """,
            [table],
        )
        print(f"\n{table}")
        for column_name, data_type, is_nullable in cursor.fetchall():
            print(f"  {column_name}: {data_type}, nullable={is_nullable}")
