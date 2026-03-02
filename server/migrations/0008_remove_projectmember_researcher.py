from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("workflow_app", "0007_projectmember_user_and_researcher_user_mapping"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="projectmember",
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name="projectmember",
            name="researcher",
        ),
    ]
