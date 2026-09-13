#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python manage.py migrate
python manage.py seed_demo
python manage.py seed_users
trap 'kill 0' EXIT
python manage.py simulate_live --interval 3 &
python manage.py runserver 127.0.0.1:8000
