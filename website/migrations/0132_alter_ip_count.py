# Generated by Django 5.0.7 on 2024-08-13 18:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0131_userprofile_modified"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ip",
            name="count",
            field=models.BigIntegerField(default=1),
        ),
    ]