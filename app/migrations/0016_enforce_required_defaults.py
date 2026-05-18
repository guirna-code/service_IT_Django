from django.db import migrations


def enforce_required_defaults(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute("UPDATE app_utilisateur SET role = 'client' WHERE role IS NULL OR role = ''")
    schema_editor.execute("ALTER TABLE app_utilisateur ALTER COLUMN role SET DEFAULT 'client'")
    schema_editor.execute("ALTER TABLE app_utilisateur ALTER COLUMN role SET NOT NULL")

    schema_editor.execute(
        "UPDATE app_rapportintervention SET statut = 'en_cours' WHERE statut IS NULL OR statut = ''"
    )
    schema_editor.execute("ALTER TABLE app_rapportintervention ALTER COLUMN statut SET DEFAULT 'en_cours'")
    schema_editor.execute("ALTER TABLE app_rapportintervention ALTER COLUMN statut SET NOT NULL")


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0015_add_performance_indexes"),
    ]

    operations = [
        migrations.RunPython(enforce_required_defaults, reverse_code=migrations.RunPython.noop),
    ]
