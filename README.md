# IIAMS — Intelligent Inventory and Asset Management System

IIAMS is a Django-based internal operations platform for asset management, inventory, maintenance, procurement, RBAC, audit logging, and an autonomous IoT/business simulation.

## Stack

- Python 3.12+ recommended
- Django 5.2
- Django REST Framework
- HTML5 / CSS / JavaScript
- SQLite for development
- PostgreSQL recommended for production

## Run the demo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start_iiams.sh
```

The launcher applies migrations, creates demo data, starts the continuous simulation engine, and starts Django.

Open: `http://127.0.0.1:8000/`

## Demo accounts

Password for all accounts: `Iiams@2026`

- `admin` — System Admin
- `manager` — Manager
- `warehouse` — Warehouse Staff
- `procurement` — Procurement
- `technician` — Technician
- `auditor` — Auditor

## Live simulation

The simulation is intentionally autonomous. The background command:

```bash
python manage.py simulate_live --interval 2
```

runs continuously and generates sensor readings and business activity. The Simulation page polls the live feed every second and updates the UI without a page refresh.

The engine can simulate:

- Sensor telemetry
- Predictive maintenance alerts
- Automatic maintenance work orders
- Inventory issues and receipts
- Asset assignments to employees
- Purchase orders
- Maintenance progress and completion
- Audit events

For a real 24/7 deployment, run `simulate_live` as a systemd service or a dedicated worker process rather than inside the web server.

## Project direction

Recommended next production upgrades:

1. PostgreSQL
2. Fine-grained permission objects
3. WebSocket/SSE transport for true push updates
4. ML predictive maintenance model
5. MQTT IoT ingestion
6. PDF/Excel reporting
7. Security monitoring and login anomaly detection
8. Docker + Nginx + Gunicorn deployment


## Live Operations Simulation

The live engine is designed as an autonomous warehouse/company simulation. It does not repeatedly mutate the same demo item just to make the screen move. The database contains a larger catalog of inventory SKUs, and the engine generates real inbound receiving and outbound issuing transactions.

Run it alongside Django:

```bash
python manage.py simulate_live --interval 3
```

Each engine cycle represents an accelerated business minute and creates 1-3 stock movements on average. The browser polls the feed every second and displays new transactions without a page refresh. Keep the simulation command running in the background for continuous activity.
