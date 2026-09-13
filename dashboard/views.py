from datetime import timedelta
from decimal import Decimal
from functools import wraps
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Sum, F
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from assets.models import Asset, AssetEvent, Category, Location
from inventory.models import Inventory
from maintenance.models import MaintenanceRequest
from procurement.models import Supplier, PurchaseOrder
from simulation.models import SensorReading, SimulationEvent, InventoryTransaction
from simulation.engine import run_cycle
from users.models import AuditLog, Department

from django import forms

User = get_user_model()


ROLE_PERMISSIONS = {
    'ADMIN': ['Dashboard', 'Assets', 'Inventory', 'Maintenance', 'Procurement', 'Suppliers',
              'Users & Roles', 'Audit Log', 'IoT Simulation', 'System Admin'],
    'MANAGER': ['Dashboard', 'Assets', 'Inventory', 'Maintenance', 'Procurement', 'Suppliers', 'Audit Log'],
    'WAREHOUSE': ['Dashboard', 'Assets', 'Inventory'],
    'PROCUREMENT': ['Dashboard', 'Inventory', 'Procurement', 'Suppliers'],
    'TECHNICIAN': ['Dashboard', 'Assets', 'Maintenance', 'IoT Simulation'],
    'AUDITOR': ['Dashboard', 'Assets', 'Inventory', 'Maintenance', 'Procurement', 'Audit Log'],
}


def can_access(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles and not request.user.is_superuser:
                return HttpResponseForbidden('You do not have permission to access this area.')
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


@login_required
def home(request):
    return redirect('dashboard')


@login_required
def dashboard(request):
    inv = list(Inventory.objects.all())
    context = {
        'total_assets': Asset.objects.count(),
        'active_assets': Asset.objects.filter(status=Asset.Status.ACTIVE).count(),
        'maintenance_assets': Asset.objects.filter(status=Asset.Status.MAINTENANCE).count(),
        'retired_assets': Asset.objects.filter(status=Asset.Status.RETIRED).count(),
        'asset_value': Asset.objects.aggregate(v=Sum('current_value'))['v'] or Decimal('0'),
        'low_stock': sum(i.needs_reorder for i in inv),
        'inventory_units': sum(i.quantity_on_hand for i in inv),
        'open_work_orders': MaintenanceRequest.objects.exclude(
            status__in=[MaintenanceRequest.Status.COMPLETED, MaintenanceRequest.Status.CANCELLED]).count(),
        'pending_pos': PurchaseOrder.objects.exclude(
            status__in=[PurchaseOrder.Status.DELIVERED, PurchaseOrder.Status.CANCELLED]).count(),
        'recent_assets': Asset.objects.select_related('category', 'location').order_by('-id')[:6],
        'recent_orders': PurchaseOrder.objects.select_related('supplier').order_by('-id')[:5],
        'alerts': list(Inventory.objects.filter(quantity_on_hand__lte=0)[:5]) +
                  list(MaintenanceRequest.objects.filter(status=MaintenanceRequest.Status.OPEN).select_related('asset')[:5]),
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def assets_page(request):
    from django.db.models import Q

    qs = Asset.objects.select_related('category', 'location', 'assigned_user').all().order_by('name')
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(serial_number__icontains=q)
            | Q(tag_code__icontains=q)
            | Q(category__name__icontains=q)
            | Q(location__building__icontains=q)
            | Q(location__room__icontains=q)
            | Q(assigned_user__first_name__icontains=q)
            | Q(assigned_user__last_name__icontains=q)
        )

    if status:
        qs = qs.filter(status=status)

    can_manage = request.user.role in ['ADMIN', 'MANAGER', 'WAREHOUSE'] or request.user.is_superuser

    return render(request, 'dashboard/list.html', {
        'title': 'Assets',
        'section': 'assets',
        'items': qs,
        'search': q,
        'status_options': Asset.Status.choices,
        'selected_status': status,
        'columns': ['name', 'serial_number', 'category', 'location', 'assigned_user', 'status', 'current_value'],
        'create_url': 'asset_create',
        'can_edit': can_manage,
    })


@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(
        Asset.objects.select_related('category', 'location', 'assigned_user'),
        pk=pk,
    )
    events = AssetEvent.objects.select_related(
        'actor', 'from_location', 'to_location', 'from_user', 'to_user'
    ).filter(asset=asset)[:50]

    return render(request, 'dashboard/asset_detail.html', {
        'title': 'Asset Detail',
        'section': 'assets',
        'asset': asset,
        'events': events,
        'can_manage': request.user.role in ['ADMIN', 'MANAGER', 'WAREHOUSE'] or request.user.is_superuser,
    })


@login_required
def inventory_page(request):
    qs = Inventory.objects.select_related('category', 'supplier').all().order_by('item_name')
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    if q:
        from django.db.models import Q
        qs = qs.filter(
            Q(item_name__icontains=q)
            | Q(sku__icontains=q)
            | Q(category__name__icontains=q)
            | Q(supplier__name__icontains=q)
        )

    if status == 'LOW':
        qs = qs.filter(quantity_on_hand__lte=F('reorder_level'))
    elif status == 'IN_STOCK':
        qs = qs.filter(quantity_on_hand__gt=F('reorder_level'))

    can_manage = request.user.role in ['ADMIN', 'MANAGER', 'WAREHOUSE'] or request.user.is_superuser

    return render(request, 'dashboard/list.html', {
        'title': 'Inventory',
        'section': 'inventory',
        'items': qs,
        'search': q,
        'status_options': [('IN_STOCK', 'In Stock'), ('LOW', 'Reorder Required')],
        'selected_status': status,
        'columns': [
            'item_name',
            'sku',
            'category',
            'supplier',
            'quantity_on_hand',
            'reorder_level',
        ],
        'create_url': 'inventory_create',
        'can_edit': can_manage,
    })


@login_required
def inventory_detail(request, pk):
    item = get_object_or_404(
        Inventory.objects.select_related('category', 'supplier'),
        pk=pk,
    )
    transactions = InventoryTransaction.objects.filter(
        item=item
    )[:50]

    return render(request, 'dashboard/inventory_detail.html', {
        'title': 'Inventory Item',
        'section': 'inventory',
        'item': item,
        'transactions': transactions,
        'can_manage': request.user.role in ['ADMIN', 'MANAGER', 'WAREHOUSE'] or request.user.is_superuser,
    })


def _inventory_movement(request, pk, movement):
    if request.user.role not in ['ADMIN', 'MANAGER', 'WAREHOUSE'] and not request.user.is_superuser:
        return HttpResponseForbidden('You do not have permission to move inventory.')

    item = get_object_or_404(Inventory, pk=pk)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', '0'))
        except (TypeError, ValueError):
            quantity = 0

        reference = request.POST.get('reference', '').strip()
        department = request.POST.get('department', '').strip()

        errors = []

        if quantity <= 0:
            errors.append('Quantity must be greater than zero.')

        if movement == InventoryTransaction.Movement.OUTBOUND and quantity > item.quantity_on_hand:
            errors.append(f'Only {item.quantity_on_hand} units are currently available.')

        if not reference:
            errors.append('Reference is required.')

        if movement == InventoryTransaction.Movement.OUTBOUND and not department:
            errors.append('Department is required for an outbound issue.')

        if not errors:
            from django.db import transaction

            with transaction.atomic():
                item = Inventory.objects.select_for_update().get(pk=item.pk)

                if movement == InventoryTransaction.Movement.INBOUND:
                    item.quantity_on_hand += quantity
                else:
                    if quantity > item.quantity_on_hand:
                        errors.append(f'Only {item.quantity_on_hand} units are currently available.')
                    else:
                        item.quantity_on_hand -= quantity

                if not errors:
                    item.save(update_fields=['quantity_on_hand'])

                    movement_reference = reference
                    if department:
                        movement_reference = f'{department} · {reference}'

                    InventoryTransaction.objects.create(
                        item=item,
                        movement=movement,
                        quantity=quantity,
                        reference=movement_reference,
                        actor_name=request.user.get_full_name() or request.user.username,
                    )

                    _audit(
                        request,
                        'UPDATE',
                        'Inventory',
                        item,
                    )

                    direction = 'received into' if movement == InventoryTransaction.Movement.INBOUND else 'issued from'
                    messages.success(
                        request,
                        f'{quantity} units {direction} {item.item_name}. Current stock: {item.quantity_on_hand}.',
                    )
                    return redirect('inventory_detail', pk=item.pk)

        return render(request, 'dashboard/inventory_movement.html', {
            'title': 'Receive Stock' if movement == InventoryTransaction.Movement.INBOUND else 'Issue Stock',
            'section': 'inventory',
            'item': item,
            'movement': movement,
            'is_inbound': movement == InventoryTransaction.Movement.INBOUND,
            'errors': errors,
            'quantity': request.POST.get('quantity', ''),
            'reference': reference,
            'department': department,
        })

    return render(request, 'dashboard/inventory_movement.html', {
        'title': 'Receive Stock' if movement == InventoryTransaction.Movement.INBOUND else 'Issue Stock',
        'section': 'inventory',
        'item': item,
        'movement': movement,
        'is_inbound': movement == InventoryTransaction.Movement.INBOUND,
        'errors': [],
        'quantity': '',
        'reference': '',
        'department': '',
    })


@login_required
def inventory_receive(request, pk):
    return _inventory_movement(request, pk, InventoryTransaction.Movement.INBOUND)


@login_required
def inventory_issue(request, pk):
    return _inventory_movement(request, pk, InventoryTransaction.Movement.OUTBOUND)


@login_required
def maintenance_page(request):
    qs = MaintenanceRequest.objects.select_related('asset','technician').all()
    return render(request,'dashboard/list.html',{'title':'Maintenance Work Orders','section':'maintenance','items':qs,
        'columns': [
    'id',
    'title',
    'asset',
    'maintenance_type',
    'priority',
    'technician',
    'scheduled_date',
    'status',
    'cost',
],
        'can_edit':request.user.role in ['ADMIN','MANAGER','TECHNICIAN'] or request.user.is_superuser})


@login_required
def procurement_page(request):
    qs = PurchaseOrder.objects.select_related('supplier','requested_by').all()
    return render(request,'dashboard/list.html',{'title':'Purchase Orders','section':'procurement','items':qs,
        'columns':['id','supplier','requested_by','order_date','expected_delivery','status','total_value'],'create_url':'po_create',
        'can_edit':request.user.role in ['ADMIN','MANAGER','PROCUREMENT'] or request.user.is_superuser})


@login_required
def suppliers_page(request):
    qs=Supplier.objects.all()
    return render(request,'dashboard/list.html',{'title':'Suppliers','section':'suppliers','items':qs,
        'columns':['name','contact_person','email','phone','performance_score'],'create_url':'supplier_create','can_edit':request.user.role in ['ADMIN','MANAGER','PROCUREMENT'] or request.user.is_superuser})


@can_access('ADMIN','MANAGER','AUDITOR')
def audit_page(request):
    return render(request,'dashboard/audit.html',{'logs':AuditLog.objects.select_related('user')[:100]})


@can_access('ADMIN')
def users_page(request):
    return render(request,'dashboard/users.html',{'users':User.objects.select_related('department').all(),'departments':Department.objects.all()})


@can_access('ADMIN')
def admin_console(request):
    return render(request,'dashboard/admin_console.html',{'roles':ROLE_PERMISSIONS,'users':User.objects.all(),
        'departments':Department.objects.all(),'categories':Category.objects.all(),'locations':Location.objects.all()})


@can_access('ADMIN','TECHNICIAN')
def simulation_page(request):
    readings = SensorReading.objects.select_related('asset')[:40]
    events = SimulationEvent.objects.select_related('asset')[:40]
    return render(request, 'dashboard/simulation.html', {
        'readings': readings,
        'events': events,
        'assets': Asset.objects.all(),
    })


@can_access('ADMIN', 'TECHNICIAN')
def simulation_feed(request):
    """Live operations feed. The UI polls this endpoint without page refresh."""
    since = request.GET.get('since')
    qs = SimulationEvent.objects.select_related('asset').all()
    if since:
        try:
            qs = qs.filter(id__gt=int(since))
        except (ValueError, TypeError):
            pass

    events = list(qs[:30])[::-1]
    latest = SimulationEvent.objects.first()
    latest_reading = SensorReading.objects.select_related('asset').first()
    minute_ago = timezone.now() - timedelta(minutes=1)
    tx_qs = InventoryTransaction.objects.select_related('item').filter(created_at__gte=minute_ago)
    inbound = tx_qs.filter(movement=InventoryTransaction.Movement.INBOUND)
    outbound = tx_qs.filter(movement=InventoryTransaction.Movement.OUTBOUND)

    return JsonResponse({
        'server_time': timezone.now().isoformat(),
        'latest_event_id': latest.id if latest else 0,
        'engine_alive': bool(latest and latest.created_at >= timezone.now() - timedelta(seconds=8)),
        'events': [{
            'id': e.id,
            'time': timezone.localtime(e.created_at).strftime('%H:%M:%S'),
            'type': e.event_type.replace('_', ' ').title(),
            'message': e.message,
            'severity': e.severity,
            'asset': e.asset.name if e.asset else '',
            'actor': e.actor_name,
        } for e in events],
        'latest_reading': ({
            'asset': latest_reading.asset.name,
            'temperature': latest_reading.temperature,
            'vibration': latest_reading.vibration,
            'anomaly': latest_reading.is_anomaly,
            'time': timezone.localtime(latest_reading.timestamp).strftime('%H:%M:%S'),
        } if latest_reading else None),
        'inventory_flow': {
            'transactions': tx_qs.count(),
            'inbound_transactions': inbound.count(),
            'outbound_transactions': outbound.count(),
            'inbound_units': sum(x.quantity for x in inbound),
            'outbound_units': sum(x.quantity for x in outbound),
            'low_stock': Inventory.objects.filter(quantity_on_hand__lte=F('reorder_level')).count(),
        },
        'recent_transactions': [{
            'id': t.id,
            'time': timezone.localtime(t.created_at).strftime('%H:%M:%S'),
            'movement': t.movement,
            'quantity': t.quantity,
            'item': t.item.item_name,
            'sku': t.item.sku,
            'reference': t.reference,
            'actor': t.actor_name,
        } for t in tx_qs[:20]],
    })


@can_access('ADMIN', 'TECHNICIAN')
def simulation_tick(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    result = run_cycle()
    return JsonResponse(result)


@login_required
def settings_page(request):
    return render(request,'dashboard/settings.html')


def _audit(request, action, table, obj):
    AuditLog.objects.create(user=request.user, action=action, table_affected=table,
                            record_id=str(obj.pk), ip_address=request.META.get('REMOTE_ADDR'))


class AssetForm(forms.ModelForm):
    class Meta:
        model=Asset
        fields=['name','category','serial_number','location','assigned_user','purchase_date','purchase_cost','current_value','status']


class AssetAssignmentForm(forms.Form):
    assigned_user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        empty_label='Select employee',
        label='Assigned employee',
    )
    note = forms.CharField(max_length=255, required=False, label='Note')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_user'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')


class AssetTransferForm(forms.Form):
    location = forms.ModelChoiceField(
        queryset=Location.objects.all().order_by('building', 'floor', 'room'),
        empty_label='Select location',
        label='New location',
    )
    note = forms.CharField(max_length=255, required=False, label='Note')


class AssetStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Asset.Status.choices, label='New status')
    note = forms.CharField(max_length=255, required=False, label='Note')


@login_required
def asset_assign(request, pk):
    if request.user.role not in ['ADMIN', 'MANAGER', 'WAREHOUSE'] and not request.user.is_superuser:
        return HttpResponseForbidden()

    asset = get_object_or_404(Asset.objects.select_related('assigned_user', 'location'), pk=pk)
    old_user = asset.assigned_user
    form = AssetAssignmentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        new_user = form.cleaned_data['assigned_user']
        note = form.cleaned_data['note']
        asset.assigned_user = new_user
        asset.last_seen = timezone.now()
        asset.save(update_fields=['assigned_user', 'last_seen'])

        AssetEvent.objects.create(
            asset=asset,
            event_type=AssetEvent.EventType.ASSIGNED,
            actor=request.user,
            from_location=asset.location,
            to_location=asset.location,
            from_user=old_user,
            to_user=new_user,
            note=note,
        )
        _audit(request, 'UPDATE', 'Asset', asset)
        messages.success(request, f'{asset.name} is now assigned to {new_user.get_full_name() or new_user.username}.')
        return redirect('asset_detail', pk=asset.pk)

    return render(request, 'dashboard/asset_action.html', {
        'title': 'Assign Asset', 'section': 'assets', 'asset': asset, 'form': form,
        'action_label': 'Assign Asset', 'back_url': 'asset_detail',
    })


@login_required
def asset_unassign(request, pk):
    if request.user.role not in ['ADMIN', 'MANAGER', 'WAREHOUSE'] and not request.user.is_superuser:
        return HttpResponseForbidden()

    asset = get_object_or_404(Asset.objects.select_related('assigned_user', 'location'), pk=pk)

    if request.method == 'POST':
        old_user = asset.assigned_user
        if old_user:
            asset.assigned_user = None
            asset.last_seen = timezone.now()
            asset.save(update_fields=['assigned_user', 'last_seen'])
            AssetEvent.objects.create(
                asset=asset,
                event_type=AssetEvent.EventType.UNASSIGNED,
                actor=request.user,
                from_location=asset.location,
                to_location=asset.location,
                from_user=old_user,
                to_user=None,
                note=request.POST.get('note', '').strip(),
            )
            _audit(request, 'UPDATE', 'Asset', asset)
            messages.success(request, f'{asset.name} has been unassigned.')
        else:
            messages.info(request, f'{asset.name} is not currently assigned.')
        return redirect('asset_detail', pk=asset.pk)

    return render(request, 'dashboard/asset_action.html', {
        'title': 'Unassign Asset', 'section': 'assets', 'asset': asset,
        'confirm_only': True, 'action_label': 'Unassign Asset',
        'back_url': 'asset_detail',
    })


@login_required
def asset_transfer(request, pk):
    if request.user.role not in ['ADMIN', 'MANAGER', 'WAREHOUSE'] and not request.user.is_superuser:
        return HttpResponseForbidden()

    asset = get_object_or_404(Asset.objects.select_related('location', 'assigned_user'), pk=pk)
    old_location = asset.location
    form = AssetTransferForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        new_location = form.cleaned_data['location']
        note = form.cleaned_data['note']
        asset.location = new_location
        asset.last_seen = timezone.now()
        asset.save(update_fields=['location', 'last_seen'])
        AssetEvent.objects.create(
            asset=asset,
            event_type=AssetEvent.EventType.TRANSFERRED,
            actor=request.user,
            from_location=old_location,
            to_location=new_location,
            from_user=asset.assigned_user,
            to_user=asset.assigned_user,
            note=note,
        )
        _audit(request, 'UPDATE', 'Asset', asset)
        messages.success(request, f'{asset.name} was transferred to {new_location}.')
        return redirect('asset_detail', pk=asset.pk)

    return render(request, 'dashboard/asset_action.html', {
        'title': 'Transfer Asset', 'section': 'assets', 'asset': asset, 'form': form,
        'action_label': 'Transfer Asset', 'back_url': 'asset_detail',
    })


@login_required
def asset_status(request, pk):
    if request.user.role not in ['ADMIN', 'MANAGER', 'WAREHOUSE'] and not request.user.is_superuser:
        return HttpResponseForbidden()

    asset = get_object_or_404(Asset, pk=pk)
    form = AssetStatusForm(request.POST or None, initial={'status': asset.status})

    if request.method == 'POST' and form.is_valid():
        old_status = asset.status
        new_status = form.cleaned_data['status']
        note = form.cleaned_data['note']
        asset.status = new_status
        asset.last_seen = timezone.now()
        asset.save(update_fields=['status', 'last_seen'])
        if old_status != new_status or note:
            AssetEvent.objects.create(
                asset=asset,
                event_type=AssetEvent.EventType.STATUS_CHANGED,
                actor=request.user,
                from_status=old_status,
                to_status=new_status,
                from_location=asset.location,
                to_location=asset.location,
                from_user=asset.assigned_user,
                to_user=asset.assigned_user,
                note=note,
            )
        _audit(request, 'UPDATE', 'Asset', asset)
        messages.success(request, f'{asset.name} status updated to {asset.get_status_display()}.')
        return redirect('asset_detail', pk=asset.pk)

    return render(request, 'dashboard/asset_action.html', {
        'title': 'Change Asset Status', 'section': 'assets', 'asset': asset, 'form': form,
        'action_label': 'Save Status', 'back_url': 'asset_detail',
    })


class InventoryForm(forms.ModelForm):
    class Meta:
        model=Inventory
        fields=['item_name','category','sku','supplier','quantity_on_hand','reorder_level','reorder_qty']


class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = [
            'asset',
            'maintenance_type',
            'priority',
            'status',
            'title',
            'description',
            'technician',
            'requested_by',
            'scheduled_date',
            'started_at',
            'completed_at',
            'cost',
            'resolution_notes',
        ]
        widgets = {
            'scheduled_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            ),
            'started_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            ),
            'completed_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            ),
            'description': forms.Textarea(
                attrs={'rows': 4}
            ),
            'resolution_notes': forms.Textarea(
                attrs={'rows': 4}
            ),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model=Supplier
        fields=['name','contact_person','email','phone','performance_score']


class POForm(forms.ModelForm):
    class Meta:
        model=PurchaseOrder
        fields=['supplier','requested_by','expected_delivery','status','total_value']
        widgets={'expected_delivery':forms.DateInput(attrs={'type':'date'})}


def _form_page(request, form, title, back_url, instance=None, table=''):
    if request.method == 'POST':
        if form.is_valid():
            obj=form.save()
            _audit(request, 'UPDATE' if instance else 'CREATE', table, obj)
            messages.success(request, f'{title} saved successfully.')
            return redirect(back_url)
    return render(request,'dashboard/form.html',{'form':form,'title':title,'back_url':back_url})


@login_required
def asset_create(request):
    if request.user.role not in ['ADMIN','MANAGER','WAREHOUSE'] and not request.user.is_superuser: return HttpResponseForbidden()
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            obj = form.save()
            AssetEvent.objects.create(
                asset=obj,
                event_type=AssetEvent.EventType.REGISTERED,
                actor=request.user,
                to_location=obj.location,
                to_user=obj.assigned_user,
                to_status=obj.status,
                note='Asset registered in IIAMS.',
            )
            _audit(request, 'CREATE', 'Asset', obj)
            messages.success(request, f'{obj.name} registered successfully.')
            return redirect('asset_detail', pk=obj.pk)
    else:
        form = AssetForm()
    return render(request, 'dashboard/form.html', {'form': form, 'title': 'Register Asset', 'back_url': 'assets'})


@login_required
def asset_edit(request, pk):
    if request.user.role not in ['ADMIN','MANAGER','WAREHOUSE'] and not request.user.is_superuser: return HttpResponseForbidden()
    obj=get_object_or_404(Asset,pk=pk)
    if request.method == 'POST':
        old_location, old_user, old_status = obj.location, obj.assigned_user, obj.status
        form = AssetForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save()
            AssetEvent.objects.create(
                asset=obj,
                event_type=AssetEvent.EventType.UPDATED,
                actor=request.user,
                from_location=old_location,
                to_location=obj.location,
                from_user=old_user,
                to_user=obj.assigned_user,
                from_status=old_status,
                to_status=obj.status,
                note='Asset record updated.',
            )
            _audit(request, 'UPDATE', 'Asset', obj)
            messages.success(request, f'{obj.name} saved successfully.')
            return redirect('asset_detail', pk=obj.pk)
    else:
        form = AssetForm(instance=obj)
    return render(request, 'dashboard/form.html', {'form': form, 'title': 'Edit Asset', 'back_url': 'asset_detail', 'back_pk': obj.pk, 'instance': obj})


@login_required
def inventory_create(request):
    if request.user.role not in ['ADMIN','MANAGER','WAREHOUSE'] and not request.user.is_superuser: return HttpResponseForbidden()
    return _form_page(request,InventoryForm(request.POST or None),'Add Inventory Item','inventory',table='Inventory')


@login_required
def inventory_edit(request,pk):
    if request.user.role not in ['ADMIN','MANAGER','WAREHOUSE'] and not request.user.is_superuser: return HttpResponseForbidden()
    obj=get_object_or_404(Inventory,pk=pk)
    return _form_page(request,InventoryForm(request.POST or None,instance=obj),'Edit Inventory Item','inventory',obj,'Inventory')


@login_required
def maintenance_create(request):
    if request.user.role not in ['ADMIN','MANAGER','TECHNICIAN'] and not request.user.is_superuser: return HttpResponseForbidden()
    return _form_page(request,MaintenanceForm(request.POST or None),'Create Work Order','maintenance',table='Maintenance')


@login_required
def maintenance_edit(request,pk):
    if request.user.role not in ['ADMIN','MANAGER','TECHNICIAN'] and not request.user.is_superuser: return HttpResponseForbidden()
    obj=get_object_or_404(MaintenanceRequest,pk=pk)
    return _form_page(request,MaintenanceForm(request.POST or None,instance=obj),'Edit Work Order','maintenance',obj,'Maintenance')



@login_required
def supplier_create(request):
    if request.user.role not in ['ADMIN','MANAGER','PROCUREMENT'] and not request.user.is_superuser: return HttpResponseForbidden()
    return _form_page(request,SupplierForm(request.POST or None),'Add Supplier','suppliers',table='Supplier')


@login_required
def supplier_edit(request,pk):
    if request.user.role not in ['ADMIN','MANAGER','PROCUREMENT'] and not request.user.is_superuser: return HttpResponseForbidden()
    obj=get_object_or_404(Supplier,pk=pk)
    return _form_page(request,SupplierForm(request.POST or None,instance=obj),'Edit Supplier','suppliers',obj,'Supplier')


@login_required
def po_create(request):
    if request.user.role not in ['ADMIN','MANAGER','PROCUREMENT'] and not request.user.is_superuser: return HttpResponseForbidden()
    return _form_page(request,POForm(request.POST or None),'Create Purchase Order','procurement',table='PurchaseOrder')


@login_required
def po_edit(request,pk):
    if request.user.role not in ['ADMIN','MANAGER','PROCUREMENT'] and not request.user.is_superuser: return HttpResponseForbidden()
    obj=get_object_or_404(PurchaseOrder,pk=pk)
    return _form_page(request,POForm(request.POST or None,instance=obj),'Edit Purchase Order','procurement',obj,'PurchaseOrder')


@can_access('ADMIN','TECHNICIAN')
def run_simulation(request):
    assets=list(Asset.objects.filter(status__in=[Asset.Status.ACTIVE,Asset.Status.MAINTENANCE]))
    now=timezone.now()
    for asset in assets:
        temp=round(random.uniform(20,82),1)
        vibration=round(random.uniform(0.4,11),2)
        anomaly=temp>70 or vibration>8
        SensorReading.objects.create(asset=asset,temperature=temp,vibration=vibration,is_anomaly=anomaly)
        if anomaly and asset.status == Asset.Status.ACTIVE:
            asset.status=Asset.Status.MAINTENANCE
            asset.last_seen=now
            asset.save(update_fields=['status','last_seen'])
    messages.success(request, f'IoT simulation completed for {len(assets)} assets.')
    return redirect('simulation')
