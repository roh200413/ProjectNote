from django.db import migrations, models


def delete_orphan_project_note_covers(apps, schema_editor):
    Project = apps.get_model("workflow_app", "Project")
    ProjectNoteCover = apps.get_model("workflow_app", "ProjectNoteCover")

    valid_project_ids = set(Project.objects.values_list("id", flat=True))
    if not valid_project_ids:
        ProjectNoteCover.objects.all().delete()
        return

    ProjectNoteCover.objects.exclude(project_id__in=valid_project_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("workflow_app", "0016_projectnotecover_cover_image_data_url"),
    ]

    operations = [
        migrations.RunPython(delete_orphan_project_note_covers, migrations.RunPython.noop),
        migrations.AddField(
            model_name="researchnote",
            name="show_title",
            field=models.BooleanField(default=True),
        ),
    ]
