# Generated by Django 5.1 on 2024-12-19 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pong', '0018_match_duration_profile_total_time_in_game'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='player1_nickname',
            field=models.CharField(default='Unknown', max_length=15),
        ),
    ]
