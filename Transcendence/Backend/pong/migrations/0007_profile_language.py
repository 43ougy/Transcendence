# Generated by Django 5.1.2 on 2024-11-20 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pong', '0006_profile_is_2fa_enabled_profile_two_fa_secret'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='language',
            field=models.CharField(default='en', max_length=2),
        ),
    ]
