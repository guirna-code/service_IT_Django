from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_add_missing_date_to_rapport'),
    ]

    operations = [
        migrations.AddField(
            model_name="rapportintervention",
            name="type",
            field=models.CharField(
                max_length=50,
                choices=[
                    ("maintenance", "Maintenance"),
                    ("reparation", "Réparation"),
                    ("installation", "Installation"),
                ],
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="rapportintervention",
            name="statut",
            field=models.CharField(
                max_length=50,
                choices=[
                    ("en_cours", "En cours"),
                    ("terminee", "Terminée"),
                    ("annulee", "Annulée"),
                    ("echec", "Échec"),
                ],
                default="en_cours",
            ),
        ),
        migrations.AddField(
            model_name="rapportintervention",
            name="duree",
            field=models.PositiveIntegerField(
                verbose_name="Durée (min)",
                null=True,
                blank=True,
            ),
        ),
        
    ]