from django.db import migrations, models


def add_field_if_missing(apps, schema_editor, model_name, field):
    model = apps.get_model("app", model_name)
    field.set_attributes_from_name(field.name)

    with schema_editor.connection.cursor() as cursor:
        columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                model._meta.db_table,
            )
        }

    if field.column not in columns:
        schema_editor.add_field(model, field)


def sync_legacy_columns(apps, schema_editor):
    add_field_if_missing(
        apps,
        schema_editor,
        "Composant",
        models.CharField(name="marque", max_length=100, null=True, blank=True),
    )
    add_field_if_missing(
        apps,
        schema_editor,
        "Composant",
        models.CharField(name="numero_serie", max_length=100, null=True, blank=True),
    )
    add_field_if_missing(
        apps,
        schema_editor,
        "Composant",
        models.DateField(name="date_installation", null=True, blank=True),
    )
    add_field_if_missing(
        apps,
        schema_editor,
        "RapportIntervention",
        models.DateTimeField(name="date_cloture", null=True, blank=True),
    )

    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("ALTER TABLE app_rapportintervention ALTER COLUMN type DROP DEFAULT")
        schema_editor.execute("ALTER TABLE app_rapportintervention ALTER COLUMN statut SET DEFAULT 'en_cours'")

        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM app_rapportintervention WHERE machine_concernee_id IS NULL"
            )
            null_machine_count = cursor.fetchone()[0]

        if null_machine_count == 0:
            schema_editor.execute(
                "ALTER TABLE app_rapportintervention ALTER COLUMN machine_concernee_id SET NOT NULL"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0013_alter_machine_etat_alter_machine_pole_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(sync_legacy_columns, reverse_code=migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="composant",
                    name="marque",
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name="composant",
                    name="numero_serie",
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name="composant",
                    name="date_installation",
                    field=models.DateField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="rapportintervention",
                    name="date_cloture",
                    field=models.DateTimeField(blank=True, null=True),
                ),
            ],
        ),
    ]
