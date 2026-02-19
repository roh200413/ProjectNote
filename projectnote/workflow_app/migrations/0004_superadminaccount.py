from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow_app", "0003_team_join_code_useraccount"),
    ]

    operations = [
        migrations.CreateModel(
            name="SuperAdminAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("username", models.CharField(max_length=80, unique=True)),
                ("display_name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("password", models.CharField(max_length=255)),
                ("organization", models.CharField(default="ProjectNote", max_length=255)),
                ("major", models.CharField(default="관리", max_length=255)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
