from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workflow_app", "0017_researchnote_show_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="researchnotefile",
            name="original_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="researchnotefile",
            name="storage_key",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
