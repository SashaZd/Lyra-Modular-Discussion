# Generated by Django 4.2 on 2023-05-05 18:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Lyra', '0002_simulation_version_simulationrun_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='simulation',
            name='notes',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]