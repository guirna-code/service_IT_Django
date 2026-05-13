from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ('app', '0009_alter_rapportintervention_options_and_more'),
]

    operations = [
        migrations.AddField(
            model_name='rapportintervention',
            name='date',
            field=models.DateField(
                null=True,
                blank=True
            ),
        ),
    ]