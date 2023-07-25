# Generated by Django 4.2 on 2023-07-24 22:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Lyra', '0002_objectofdiscussion_attitude_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='objectofdiscussion',
            name='attitude',
            field=models.FloatField(default=0.64),
        ),
        migrations.AlterField(
            model_name='objectofdiscussion',
            name='opinion',
            field=models.FloatField(default=-0.29),
        ),
        migrations.AlterField(
            model_name='view',
            name='attitude',
            field=models.FloatField(default=-0.95),
        ),
        migrations.AlterField(
            model_name='view',
            name='ood',
            field=models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='Lyra.objectofdiscussion'),
        ),
        migrations.AlterField(
            model_name='view',
            name='opinion',
            field=models.FloatField(default=0.04),
        ),
        migrations.AlterField(
            model_name='view',
            name='private_acceptance_thresh',
            field=models.FloatField(default=0.66),
        ),
        migrations.AlterField(
            model_name='view',
            name='topic',
            field=models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='Lyra.topic'),
        ),
        migrations.AlterField(
            model_name='view',
            name='uncertainty',
            field=models.FloatField(default=0.21),
        ),
    ]