from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("workflow_app", "0005_drop_adminaccount_rename_team_table"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="company",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="projects", to="workflow_app.team"),
        ),
        migrations.RemoveField(
            model_name="signaturestate",
            name="last_signed_by",
        ),
        migrations.AddField(
            model_name="signaturestate",
            name="signature_data_url",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="signaturestate",
            name="user",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="signature_state", to="workflow_app.useraccount"),
        ),
    ]
