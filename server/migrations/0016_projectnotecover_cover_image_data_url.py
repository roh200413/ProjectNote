from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workflow_app", "0015_projectnotecover"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectnotecover",
            name="cover_image_data_url",
            field=models.TextField(blank=True, default=""),
        ),
    ]
