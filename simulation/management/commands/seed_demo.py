from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from assets.models import Category, Location, Asset
from inventory.models import Inventory
from procurement.models import Supplier, PurchaseOrder
from maintenance.models import Maintenance
from users.models import Department

User=get_user_model()
class Command(BaseCommand):
    help='Create realistic demo data for IIAMS.'
    def handle(self,*args,**kwargs):
        depts={}
        for name,loc in [('IT Operations','Riyadh HQ'),('Warehouse','Riyadh DC'),('Procurement','Riyadh HQ'),('Maintenance','Riyadh HQ'),('Internal Audit','Riyadh HQ')]:
            depts[name]=Department.objects.get_or_create(dept_name=name,defaults={'location':loc})[0]
        users=[
            ('admin','System','Admin','ADMIN',True,'IT Operations'),
            ('manager','Sara','Alqahtani','MANAGER',False,'IT Operations'),
            ('warehouse','Faisal','Alharbi','WAREHOUSE',False,'Warehouse'),
            ('procurement','Noura','Alotaibi','PROCUREMENT',False,'Procurement'),
            ('technician','Yousef','Alzahrani','TECHNICIAN',False,'Maintenance'),
            ('auditor','Reem','Alshehri','AUDITOR',False,'Internal Audit'),
        ]
        created={}
        for username,first,last,role,superuser,dept in users:
            u,_=User.objects.get_or_create(username=username,defaults={'first_name':first,'last_name':last,'email':f'{username}@iiams.local'})
            u.first_name,u.last_name,u.role,u.department=first,last,role,depts[dept]
            u.is_staff=superuser;u.is_superuser=superuser;u.is_active=True;u.set_password('Iiams@2026');u.save();created[username]=u
        cats={}
        for n in ['Laptops','Networking','Servers','Mobile Devices','Office Equipment']:
            cats[n]=Category.objects.get_or_create(name=n)[0]
        locs={}
        for b,f,r in [('HQ Building','2','IT-201'),('HQ Building','3','Server-01'),('Distribution Center','1','WH-04'),('HQ Building','1','Proc-08')]:
            locs[r]=Location.objects.get_or_create(building=b,floor=f,room=r)[0]
        assets=[
            ('Dell Latitude 7450','DL-7450-001', 'Laptops','IT-201',created['manager'],8200,6900,Asset.Status.ACTIVE),
            ('Cisco Catalyst 9300','C9K-9300-014','Networking','Server-01',None,14500,11200,Asset.Status.ACTIVE),
            ('HPE ProLiant DL380','HP-DL380-022','Servers','Server-01',created['technician'],32500,24800,Asset.Status.MAINTENANCE),
            ('iPhone 16 Pro','APL-IP16-008','Mobile Devices','Proc-08',created['procurement'],5200,4700,Asset.Status.ACTIVE),
            ('Zebra TC58 Scanner','ZBR-TC58-031','Mobile Devices','WH-04',created['warehouse'],3100,2700,Asset.Status.ACTIVE),
            ('Lenovo ThinkPad T14','LN-T14-117','Laptops','IT-201',created['manager'],6100,4800,Asset.Status.ACTIVE),
        ]
        for name,serial,cat,room,user,cost,val,status in assets:
            Asset.objects.update_or_create(serial_number=serial,defaults={'name':name,'category':cats[cat],'location':locs[room],'assigned_user':user,'purchase_date':date.today()-timedelta(days=420),'purchase_cost':cost,'current_value':val,'status':status})
        suppliers=[]
        for name,score in [('Gulf Tech Supplies',94),('Riyadh Network Solutions',91),('Al Noor Office Systems',87),('Enterprise Devices Co.',96)]:
            suppliers.append(Supplier.objects.get_or_create(name=name,defaults={'performance_score':score,'contact_person':'Account Manager','email':name.lower().replace(' ','')+'@example.local'})[0])
        inv=[
            ('Cat6 Ethernet Cable 305m','CAB-CAT6-305','Networking',suppliers[1],180,35,120),
            ('8GB DDR5 SODIMM','RAM-DDR5-8','Servers',suppliers[0],240,60,180),
            ('16GB DDR5 SODIMM','RAM-DDR5-16','Servers',suppliers[0],165,45,120),
            ('32GB DDR5 ECC DIMM','RAM-DDR5-ECC32','Servers',suppliers[0],96,25,60),
            ('Laptop Dock USB-C','DOC-USBC-01','Laptops',suppliers[2],84,20,60),
            ('Zebra Scanner Battery','ZBR-BAT-58','Mobile Devices',suppliers[3],125,30,80),
            ('SSD 1TB NVMe','SSD-NVME-1T','Servers',suppliers[0],72,18,50),
            ('SSD 2TB NVMe','SSD-NVME-2T','Servers',suppliers[0],44,12,35),
            ('HDMI Cable 2m','CAB-HDMI-2M','Office Equipment',suppliers[2],260,50,160),
            ('DisplayPort Cable 2m','CAB-DP-2M','Office Equipment',suppliers[2],190,40,120),
            ('USB-C Cable 1m','CAB-USBC-1M','Office Equipment',suppliers[2],320,70,200),
            ('USB-A to USB-C Adapter','ADP-USBA-USBC','Office Equipment',suppliers[2],145,35,90),
            ('Wireless Keyboard','KB-WL-01','Office Equipment',suppliers[2],110,25,70),
            ('Wireless Mouse','MS-WL-01','Office Equipment',suppliers[2],175,35,100),
            ('Laptop Charger 65W','CHG-LAP-65W','Laptops',suppliers[3],92,20,60),
            ('Laptop Charger 90W','CHG-LAP-90W','Laptops',suppliers[3],64,16,45),
            ('Laptop Sleeve 15-inch','SLV-LAP-15','Laptops',suppliers[2],135,30,80),
            ('RJ45 Connector Pack','NET-RJ45-100','Networking',suppliers[1],420,80,250),
            ('Keystone Jack Cat6','NET-KJ-C6','Networking',suppliers[1],210,45,140),
            ('SFP 1G Multimode','SFP-1G-MM','Networking',suppliers[1],58,12,35),
            ('SFP 10G SR','SFP-10G-SR','Networking',suppliers[1],37,10,25),
            ('Cisco Console Cable','NET-CNSL-01','Networking',suppliers[1],76,18,50),
            ('Rack Power Strip','RACK-PDU-8','Networking',suppliers[1],32,8,20),
            ('Patch Panel 24 Port','NET-PP-24','Networking',suppliers[1],28,7,18),
            ('UPS Battery 12V','UPS-BAT-12V','Servers',suppliers[0],51,12,30),
            ('Server Fan Module','SRV-FAN-DL380','Servers',suppliers[0],23,6,15),
            ('Server Rail Kit','SRV-RAIL-DL380','Servers',suppliers[0],19,5,12),
            ('Thermal Paste 5g','THERMAL-5G','Servers',suppliers[0],88,20,50),
            ('iPhone USB-C Adapter','MOB-IPH-ADP','Mobile Devices',suppliers[3],105,25,70),
            ('iPhone Protective Case','MOB-IPH-CASE','Mobile Devices',suppliers[3],210,50,140),
            ('Screen Protector Pack','MOB-SP-10','Mobile Devices',suppliers[3],170,40,100),
            ('Zebra TC58 Hand Strap','ZBR-STRAP-58','Mobile Devices',suppliers[3],115,25,70),
            ('Printer Toner Black','PRT-TON-BLK','Office Equipment',suppliers[2],47,12,30),
            ('Printer Toner Cyan','PRT-TON-CYN','Office Equipment',suppliers[2],31,8,20),
            ('A4 Paper Box','PPR-A4-BOX','Office Equipment',suppliers[2],155,30,100),
            ('Label Roll 100x50','LBL-100X50','Office Equipment',suppliers[2],98,20,65),
            ('Barcode Label Roll','LBL-BARCODE','Office Equipment',suppliers[3],130,30,85),
            ('Ethernet Tester','NET-TESTER-01','Networking',suppliers[1],14,4,10),
            ('Cable Management Pack','CAB-MGMT-50','Networking',suppliers[1],76,18,50),
            ('ESD Wrist Strap','ESD-WRIST-01','Servers',suppliers[0],61,15,40),
        ]
        for name,sku,cat,sup,qty,level,rqty in inv:
            Inventory.objects.update_or_create(sku=sku,defaults={'item_name':name,'category':cats[cat],'supplier':sup,'quantity_on_hand':qty,'reorder_level':level,'reorder_qty':rqty})
        for i,sup in enumerate(suppliers[:3],1):
            po_status = [PurchaseOrder.Status.SENT, PurchaseOrder.Status.PARTIALLY_DELIVERED, PurchaseOrder.Status.DRAFT][i-1]
            po, _ = PurchaseOrder.objects.get_or_create(
                supplier=sup,
                requested_by=created['procurement'],
                status=po_status,
                defaults={
                    'expected_delivery': date.today() + timedelta(days=5 + i * 3),
                    'total_value': [18500, 9200, 4300][i-1],
                },
            )
        hp=Asset.objects.get(serial_number='HP-DL380-022')
        Maintenance.objects.get_or_create(asset=hp,status=Maintenance.Status.OPEN,defaults={'technician':created['technician'],'scheduled_date':date.today()+timedelta(days=2),'description':'High vibration reading detected during routine monitoring. Inspect cooling and storage subsystem.','cost':1250})
        self.stdout.write(self.style.SUCCESS('Demo data is ready. All demo users use password: Iiams@2026'))
