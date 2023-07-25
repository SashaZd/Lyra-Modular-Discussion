# Generated by Django 4.2 on 2023-07-24 22:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Lyra', '0003_alter_objectofdiscussion_attitude_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='objectofdiscussion',
            name='attitude',
            field=models.FloatField(default=0.41),
        ),
        migrations.AlterField(
            model_name='objectofdiscussion',
            name='opinion',
            field=models.FloatField(default=-0.08),
        ),
        migrations.AlterField(
            model_name='view',
            name='attitude',
            field=models.FloatField(default=-0.2),
        ),
        migrations.AlterField(
            model_name='view',
            name='ood',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='Lyra.objectofdiscussion'),
        ),
        migrations.AlterField(
            model_name='view',
            name='opinion',
            field=models.FloatField(default=0.78),
        ),
        migrations.AlterField(
            model_name='view',
            name='private_acceptance_thresh',
            field=models.FloatField(default=0.23),
        ),
        migrations.AlterField(
            model_name='view',
            name='topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Lyra.topic'),
        ),
        migrations.AlterField(
            model_name='view',
            name='uncertainty',
            field=models.FloatField(default=0.41),
        ),
    ]
