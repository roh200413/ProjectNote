from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow_app", "0016_projectnotecover_cover_image_data_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="researchnote",
            name="show_title",
            field=models.BooleanField(default=True),
        ),
    ]
