from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0009_alter_rapportintervention_options_and_more"),
    ]

    # The current 0009 migration already adds RapportIntervention.date.
    # Keep this migration as an explicit no-op so already-applied databases and
    # fresh installs share the same migration graph without duplicate columns.
    operations = []
