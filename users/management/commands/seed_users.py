from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Department

User = get_user_model()
DEFAULT_PASSWORD = "Iiams@2026"
SEED_USERS = [
    ("admin", "System", "Admin", "admin@iiams.local", User.Role.ADMIN, True, True, "IT Department"),
    ("manager", "Sara", "Alqahtani", "manager@iiams.local", User.Role.MANAGER, False, True, "Operations"),
    ("warehouse", "Faisal", "Alharbi", "warehouse@iiams.local", User.Role.WAREHOUSE, False, False, "Warehouse"),
    ("procurement", "Noura", "Alotaibi", "procurement@iiams.local", User.Role.PROCUREMENT, False, False, "Procurement"),
    ("technician", "Yousef", "Alzahrani", "technician@iiams.local", User.Role.TECHNICIAN, False, False, "Maintenance"),
    ("auditor", "Reem", "Alshehri", "auditor@iiams.local", User.Role.AUDITOR, False, False, "Internal Audit"),
]

class Command(BaseCommand):
    help = "Create one demo user for each IIAMS role."
    def add_arguments(self, parser):
        parser.add_argument("--password", type=str, default=DEFAULT_PASSWORD, help="Password used for demo accounts.")
    def handle(self, *args, **options):
        password = options["password"]
        for username, first_name, last_name, email, role, is_super, is_staff, dept_name in SEED_USERS:
            department, _ = Department.objects.get_or_create(dept_name=dept_name, defaults={"location": "Riyadh, Saudi Arabia"})
            user, created = User.objects.get_or_create(username=username, defaults={"first_name":first_name,"last_name":last_name,"email":email,"role":role,"department":department,"is_superuser":is_super,"is_staff":is_staff,"is_active":True})
            user.first_name=first_name; user.last_name=last_name; user.email=email; user.role=role; user.department=department; user.is_superuser=is_super; user.is_staff=is_staff; user.is_active=True
            user.set_password(password); user.save()
            self.stdout.write(self.style.SUCCESS(f"{username}: {'created' if created else 'updated'}"))
        self.stdout.write(self.style.SUCCESS("All demo accounts are ready."))
