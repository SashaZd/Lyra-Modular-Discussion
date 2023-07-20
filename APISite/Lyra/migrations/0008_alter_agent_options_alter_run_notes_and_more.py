# Generated by Django 4.2 on 2023-07-06 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Lyra', '0007_rename_actions_action'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='agent',
            options={'ordering': ('-id',)},
        ),
        migrations.AlterField(
            model_name='run',
            name='notes',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AlterField(
            model_name='simulation',
            name='title',
            field=models.CharField(blank=True, default='Unnamed', max_length=100, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='agent',
            unique_together={('run', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='run',
            unique_together={('simulation', 'number')},
        ),
    ]
