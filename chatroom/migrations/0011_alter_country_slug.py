# Generated by Django 4.1.7 on 2023-04-03 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chatroom", "0010_directmessageuser_is_accepted"),
    ]

    operations = [
        migrations.AlterField(
            model_name="country",
            name="slug",
            field=models.SlugField(blank=True, max_length=220, unique=True),
        ),
    ]
