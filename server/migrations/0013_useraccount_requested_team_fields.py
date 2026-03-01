from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workflow_app", "0012_alter_useraccount_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="useraccount",
            name="requested_team_description",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="useraccount",
            name="requested_team_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
    ]
