# Generated by Django 4.2 on 2023-07-17 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Lyra', '0017_viewhistories_remove_view_view_ood_or_topic_not_null_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='viewhistories',
            old_name='views',
            new_name='view',
        ),
        migrations.AlterField(
            model_name='view',
            name='attitude',
            field=models.FloatField(default=-0.2),
        ),
        migrations.AlterField(
            model_name='view',
            name='opinion',
            field=models.FloatField(default=0.46),
        ),
        migrations.AlterField(
            model_name='view',
            name='private_acceptance_thresh',
            field=models.FloatField(default=0.63),
        ),
        migrations.AlterField(
            model_name='view',
            name='uncertainty',
            field=models.FloatField(default=0.67),
        ),
    ]
