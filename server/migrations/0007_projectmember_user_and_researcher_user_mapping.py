from django.db import migrations, models
import django.db.models.deletion


def backfill_user_links(apps, schema_editor):
    UserAccount = apps.get_model("workflow_app", "UserAccount")
    Researcher = apps.get_model("workflow_app", "Researcher")
    ProjectMember = apps.get_model("workflow_app", "ProjectMember")

    users_by_email = {u.email.lower(): u for u in UserAccount.objects.exclude(email="")}

    for researcher in Researcher.objects.filter(user__isnull=True):
        user = users_by_email.get((researcher.email or "").lower())
        if user:
            researcher.user_id = user.id
            researcher.save(update_fields=["user"])

    for member in ProjectMember.objects.filter(user__isnull=True).select_related("researcher"):
        researcher = member.researcher
        user = None
        if getattr(researcher, "user_id", None):
            user = UserAccount.objects.filter(id=researcher.user_id).first()
        if not user and researcher and researcher.email:
            user = users_by_email.get(researcher.email.lower())
        if user:
            member.user_id = user.id
            member.save(update_fields=["user"])


class Migration(migrations.Migration):

    dependencies = [
        ("workflow_app", "0006_project_company_and_user_signature"),
    ]

    operations = [
        migrations.AddField(
            model_name="researcher",
            name="user",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="researcher_profile", to="workflow_app.useraccount"),
        ),
        migrations.AddField(
            model_name="projectmember",
            name="user",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="project_memberships", to="workflow_app.useraccount"),
        ),
        migrations.AddConstraint(
            model_name="projectmember",
            constraint=models.UniqueConstraint(fields=("project", "user"), name="unique_project_user_member"),
        ),
        migrations.RunPython(backfill_user_links, migrations.RunPython.noop),
    ]
