from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("workflow_app", "0008_remove_projectmember_researcher"),
    ]

    # NOTE:
    # `unique_together(project, researcher)` is already removed in 0008 before
    # dropping the `researcher` field to avoid SQLite table-remake errors.
    # Keep 0009 as a no-op for migration chain compatibility.
    operations = []
