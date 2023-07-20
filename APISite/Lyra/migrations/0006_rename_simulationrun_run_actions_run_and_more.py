# Generated by Django 4.2 on 2023-07-03 20:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Lyra', '0005_actions_topic_objectofdiscussion'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SimulationRun',
            new_name='Run',
        ),
        migrations.AddField(
            model_name='actions',
            name='run',
            field=models.ForeignKey(default='2', on_delete=django.db.models.deletion.CASCADE, to='Lyra.run'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='simulation',
            name='version',
            field=models.CharField(blank=True, default='1.0', max_length=10, null=True),
        ),
    ]
