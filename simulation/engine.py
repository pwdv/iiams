import random
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from assets.models import Asset
from inventory.models import Inventory
from maintenance.models import MaintenanceRequest
from procurement.models import PurchaseOrder, Supplier
from simulation.models import SensorReading, SimulationEvent, InventoryTransaction
from users.models import AuditLog, User

TEMP_THRESHOLD = 80.0
VIBRATION_THRESHOLD = 7.5
MAX_READINGS = 5000
MAX_EVENTS = 2000
MAX_TRANSACTIONS = 3000


def _event(event_type, message, severity='INFO', asset=None, actor_name='Simulation Engine'):
    return SimulationEvent.objects.create(
        event_type=event_type, message=message, severity=severity,
        asset=asset, actor_name=actor_name,
    )


def _audit(action, table, obj, actor=None):
    AuditLog.objects.create(
        user=actor, action=action, table_affected=table,
        record_id=str(obj.pk), ip_address=None,
    )


def _name(user, fallback):
    return (user.get_full_name() or user.username) if user else fallback


@transaction.atomic
def run_cycle():
    """One accelerated minute of autonomous warehouse/company activity.

    The browser can poll every second while this engine runs every 2-3 seconds.
    Inventory movement is the primary business activity: stock is physically
    received and issued rather than repeatedly changing existing asset records.
    """
    now = timezone.now()
    inventory = list(Inventory.objects.select_related('supplier', 'category').all())
    users = list(User.objects.filter(is_active=True).exclude(role=User.Role.ADMIN))
    suppliers = list(Supplier.objects.all())
    technicians = list(User.objects.filter(role=User.Role.TECHNICIAN, is_active=True))
    assets = list(Asset.objects.select_related('assigned_user').filter(
        status__in=[Asset.Status.ACTIVE, Asset.Status.MAINTENANCE]
    ))

    if not inventory:
        _event('SYSTEM', 'Warehouse is empty. Add inventory items before starting the live engine.', 'WARNING')
        return {'events': 1, 'readings': 0, 'transactions': 0}

    created_events = 0
    created_readings = 0
    created_transactions = 0

    # 1) REAL WAREHOUSE FLOW: 1-3 inbound/outbound movements per accelerated minute.
    # Outbound is demand from employees/departments; inbound is supplier receiving.
    moves = random.choices([1, 2, 3], weights=[0.25, 0.55, 0.20], k=1)[0]
    for _ in range(moves):
        item = random.choice(inventory)
        actor = random.choice(users) if users else None

        # Bias toward outbound activity, but receive stock whenever an item is low.
        force_inbound = item.needs_reorder and random.random() < 0.72
        inbound = force_inbound or random.random() < 0.38

        if inbound:
            qty = random.randint(max(4, min(8, item.reorder_qty // 2 or 4)), max(10, min(25, item.reorder_qty)))
            item.quantity_on_hand += qty
            item.save(update_fields=['quantity_on_hand'])
            reference = f'GRN-{random.randint(10000, 99999)}'
            InventoryTransaction.objects.create(
                item=item, movement=InventoryTransaction.Movement.INBOUND,
                quantity=qty, reference=reference, actor_name=_name(actor, 'Receiving Clerk')
            )
            _event(
                'STOCK_RECEIPT',
                f'{qty} units of {item.item_name} received from {item.supplier.name if item.supplier else "supplier"} ({reference}).',
                'INFO', actor_name=_name(actor, 'Receiving Clerk')
            )
        else:
            available = item.quantity_on_hand
            if available <= 0:
                # No fake negative stock: record a demand attempt instead.
                _event('STOCKOUT', f'Demand for {item.item_name} could not be fulfilled — stock is 0.', 'CRITICAL', actor_name=_name(actor, 'Warehouse Staff'))
                created_events += 1
                continue
            qty = random.randint(1, min(8, available))
            item.quantity_on_hand -= qty
            item.save(update_fields=['quantity_on_hand'])
            reference = f'ISS-{random.randint(10000, 99999)}'
            InventoryTransaction.objects.create(
                item=item, movement=InventoryTransaction.Movement.OUTBOUND,
                quantity=qty, reference=reference, actor_name=_name(actor, 'Warehouse Staff')
            )
            sev = 'WARNING' if item.needs_reorder else 'INFO'
            _event(
                'STOCK_ISSUE',
                f'{qty} units of {item.item_name} issued to an internal department ({reference}).',
                sev, actor_name=_name(actor, 'Warehouse Staff')
            )
        created_events += 1
        created_transactions += 1

    # 2) Sensor telemetry is secondary. Only occasional readings are generated.
    if assets and random.random() < 0.45:
        sample = random.sample(assets, min(len(assets), random.randint(1, 2)))
        for asset in sample:
            temperature = round(random.gauss(48, 8), 1)
            vibration = round(max(0.15, random.gauss(2.8, 1.2)), 2)
            if random.random() < 0.045:
                temperature = round(random.uniform(81, 94), 1)
            if random.random() < 0.035:
                vibration = round(random.uniform(7.7, 10.5), 2)
            anomaly = temperature > TEMP_THRESHOLD or vibration > VIBRATION_THRESHOLD
            SensorReading.objects.create(
                asset=asset, temperature=temperature, vibration=vibration, is_anomaly=anomaly
            )
            asset.last_seen = now
            asset.save(update_fields=['last_seen'])
            created_readings += 1
            if anomaly:
                opened = MaintenanceRequest.objects.filter(
    asset=asset,
    status__in=[
        MaintenanceRequest.Status.OPEN,
        MaintenanceRequest.Status.IN_PROGRESS,
    ]
).first()
                if not opened:
                    tech = random.choice(technicians) if technicians else None
                    work = MaintenanceRequest.objects.create(
    asset=asset,
    technician=tech,
    scheduled_date=now,
    status=MaintenanceRequest.Status.OPEN,
    maintenance_type=MaintenanceRequest.MaintenanceType.CORRECTIVE,
    priority=MaintenanceRequest.Priority.CRITICAL,
    title='Automatic Predictive Maintenance Alert',
    description=(
        f'Automatic predictive alert: temperature {temperature}°C, '
        f'vibration {vibration} mm/s.'
    ),
    requested_by=tech,

                    )
                    asset.status = Asset.Status.MAINTENANCE
                    asset.save(update_fields=['status'])
                    _audit('CREATE', 'MaintenanceRequest', work, tech)
                    _event('MAINTENANCE_ALERT', f'{asset.name} exceeded sensor limits. Work order #{work.pk} opened.', 'CRITICAL', asset)
                    created_events += 1

    # 3) Procurement reacts to sustained low stock, not random POs every few seconds.
    low_items = [i for i in inventory if i.needs_reorder]
    if low_items and suppliers and random.random() < 0.22:
        item = random.choice(low_items)
        supplier = item.supplier or random.choice(suppliers)
        actor = random.choice(users) if users else None
        po = PurchaseOrder.objects.create(
            supplier=supplier, requested_by=actor,
            expected_delivery=(now + timedelta(days=random.randint(2, 7))).date(),
            status=PurchaseOrder.Status.SENT,
            total_value=Decimal(random.randint(1200, 15000)),
        )
        _audit('CREATE', 'PurchaseOrder', po, actor)
        _event('REPLENISHMENT_ORDER', f'PO-{po.pk} sent for {item.item_name} replenishment.', 'WARNING', actor_name=_name(actor, 'Procurement'))
        created_events += 1

    # 4) Progress maintenance naturally.
    open_work = list(
    MaintenanceRequest.objects.filter(
        status=MaintenanceRequest.Status.OPEN
    )
)
    if open_work and random.random() < 0.20:
        work = random.choice(open_work)
        work.status = MaintenanceRequest.Status.IN_PROGRESS
        if not work.technician and technicians:
            work.technician = random.choice(technicians)
        work.save(update_fields=['status', 'technician'])
        _event('MAINTENANCE_UPDATE', f'Work order #{work.pk} moved to In Progress.', 'INFO', work.asset, _name(work.technician, 'Technician'))
        created_events += 1

    in_progress = list(
    MaintenanceRequest.objects.filter(
        status=MaintenanceRequest.Status.IN_PROGRESS
    ).order_by('id')[:10]
)
    if in_progress and random.random() < 0.12:
        work = random.choice(in_progress)
        work.status = MaintenanceRequest.Status.COMPLETED
        work.completed_at = now
        work.cost = Decimal(random.randint(250, 2500))
        work.save(update_fields=['status', 'completed_at', 'cost'])
        if work.asset.status == Asset.Status.MAINTENANCE:
            work.asset.status = Asset.Status.ACTIVE
            work.asset.save(update_fields=['status'])
        _event('MAINTENANCE_COMPLETE', f'Work order #{work.pk} completed; {work.asset.name} returned to service.', 'INFO', work.asset, _name(work.technician, 'Technician'))
        created_events += 1

    # Retention for long-running demos.
    cutoff = now - timedelta(hours=24)
    SimulationEvent.objects.filter(created_at__lt=cutoff).delete()
    SensorReading.objects.filter(timestamp__lt=cutoff).delete()
    InventoryTransaction.objects.filter(created_at__lt=cutoff).delete()

    for Model, limit, field in [
        (SimulationEvent, MAX_EVENTS, 'created_at'),
        (SensorReading, MAX_READINGS, 'timestamp'),
        (InventoryTransaction, MAX_TRANSACTIONS, 'created_at'),
    ]:
        count = Model.objects.count()
        if count > limit:
            ids = list(Model.objects.order_by(field).values_list('pk', flat=True)[:count-limit])
            Model.objects.filter(pk__in=ids).delete()

    return {
        'events': created_events,
        'readings': created_readings,
        'transactions': created_transactions,
    }
