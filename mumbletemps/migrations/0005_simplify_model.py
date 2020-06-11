# Generated by Django 2.2.13 on 2020-06-11 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mumbletemps", "0004_auto_20200605_0828"),
    ]

    operations = [
        migrations.RemoveField(model_name="tempuser", name="name",),
        migrations.AlterField(
            model_name="tempuser",
            name="expires",
            field=models.IntegerField(help_text="Unix timestamp when token expires"),
        ),
        migrations.AlterField(
            model_name="tempuser",
            name="password",
            field=models.CharField(help_text="Temporary token", max_length=20),
        ),
        migrations.AlterField(
            model_name="tempuser",
            name="username",
            field=models.CharField(
                help_text="Mumble username (will be generated using NameFormatter)",
                max_length=200,
                unique=True,
            ),
        ),
    ]
