from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0001_initial'),
        ('simulation', '0002_simulationevent'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('movement', models.CharField(choices=[('INBOUND', 'Inbound'), ('OUTBOUND', 'Outbound')], max_length=10)),
                ('quantity', models.PositiveIntegerField()),
                ('reference', models.CharField(blank=True, max_length=80)),
                ('actor_name', models.CharField(default='Warehouse Staff', max_length=120)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='simulation_transactions', to='inventory.inventory')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
