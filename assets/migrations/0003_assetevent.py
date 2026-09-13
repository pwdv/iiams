from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('assets', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('REGISTERED', 'Registered'), ('ASSIGNED', 'Assigned'), ('UNASSIGNED', 'Unassigned'), ('TRANSFERRED', 'Transferred'), ('STATUS_CHANGED', 'Status Changed'), ('UPDATED', 'Updated')], max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('from_status', models.CharField(blank=True, max_length=20)),
                ('to_status', models.CharField(blank=True, max_length=20)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asset_events', to=settings.AUTH_USER_MODEL)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='assets.asset')),
                ('from_location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asset_events_from', to='assets.location')),
                ('from_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asset_events_from_user', to=settings.AUTH_USER_MODEL)),
                ('to_location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asset_events_to', to='assets.location')),
                ('to_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asset_events_to_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at', '-id']},
        ),
    ]
