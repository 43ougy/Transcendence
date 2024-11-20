# Generated by Django 5.1.2 on 2024-11-20 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pong', '0005_gameservermodel_waitingplayermodel'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_2fa_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profile',
            name='two_fa_secret',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
