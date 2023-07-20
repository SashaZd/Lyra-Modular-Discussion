# Generated by Django 4.2 on 2023-07-13 21:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Lyra', '0015_alter_agent_unique_together_alter_view_agent_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='view',
            name='attitude',
            field=models.FloatField(default=0.04),
        ),
        migrations.AlterField(
            model_name='view',
            name='ood',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Lyra.objectofdiscussion'),
        ),
        migrations.AlterField(
            model_name='view',
            name='opinion',
            field=models.FloatField(default=-0.96),
        ),
        migrations.AlterField(
            model_name='view',
            name='private_acceptance_thresh',
            field=models.FloatField(default=0.55),
        ),
        migrations.AlterField(
            model_name='view',
            name='topic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Lyra.topic'),
        ),
        migrations.AlterField(
            model_name='view',
            name='uncertainty',
            field=models.FloatField(default=0.03),
        ),
    ]
