from django.db import migrations, models
import django.db.models.deletion


def seed_team_join_codes(apps, schema_editor):
    Team = apps.get_model('workflow_app', 'Team')
    used = set()
    for team in Team.objects.order_by('id'):
        code = str((100000 + team.id) % 1000000).zfill(6)
        while code in used:
            code = str((int(code) + 1) % 1000000).zfill(6)
        used.add(code)
        team.join_code = code
        team.save(update_fields=['join_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_app', '0002_team_adminaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='join_code',
            field=models.CharField(default='000000', max_length=6, unique=True),
            preserve_default=False,
        ),
        migrations.RunPython(seed_team_join_codes, migrations.RunPython.noop),
        migrations.CreateModel(
            name='UserAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('username', models.CharField(max_length=80, unique=True)),
                ('display_name', models.CharField(max_length=120)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=255)),
                ('role', models.CharField(choices=[('admin', '관리자'), ('member', '일반')], default='member', max_length=20)),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='members', to='workflow_app.team')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
