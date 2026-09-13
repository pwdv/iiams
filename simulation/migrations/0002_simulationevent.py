from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('assets', '0002_initial'), ('simulation', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='SimulationEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event_type', models.CharField(max_length=40)),
                ('message', models.CharField(max_length=300)),
                ('severity', models.CharField(choices=[('INFO', 'Info'), ('WARNING', 'Warning'), ('CRITICAL', 'Critical')], default='INFO', max_length=12)),
                ('actor_name', models.CharField(default='Simulation Engine', max_length=120)),
                ('asset', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='simulation_events', to='assets.asset')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
