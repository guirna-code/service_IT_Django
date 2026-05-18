from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0014_sync_legacy_schema"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="machine",
            index=models.Index(fields=["etat"], name="app_machine_etat_5ed9c9_idx"),
        ),
        migrations.AddIndex(
            model_name="machine",
            index=models.Index(fields=["type"], name="app_machine_type_f7331f_idx"),
        ),
        migrations.AddIndex(
            model_name="machine",
            index=models.Index(fields=["pole"], name="app_machine_pole_8c2b40_idx"),
        ),
        migrations.AddIndex(
            model_name="rapportintervention",
            index=models.Index(fields=["statut"], name="app_rapport_statut_ba4064_idx"),
        ),
        migrations.AddIndex(
            model_name="rapportintervention",
            index=models.Index(fields=["date"], name="app_rapport_date_4ee5a3_idx"),
        ),
    ]
