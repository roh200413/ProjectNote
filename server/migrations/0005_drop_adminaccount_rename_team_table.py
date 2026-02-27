from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("workflow_app", "0004_superadminaccount"),
    ]

    operations = [
        migrations.DeleteModel(
            name="AdminAccount",
        ),
        migrations.AlterModelTable(
            name="team",
            table="workflow_app_company",
        ),
    ]
