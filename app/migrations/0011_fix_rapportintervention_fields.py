from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0010_add_missing_date_to_rapport"),
    ]

    # The current migration history already has type/statut from 0009 and duree
    # from earlier migrations. This file remains as a no-op compatibility step
    # to avoid duplicate AddField operations on fresh databases.
    operations = []
