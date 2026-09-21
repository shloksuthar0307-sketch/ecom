#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Ensure the database schema exists before running migrations
python create_schema.py

python manage.py collectstatic --no-input
python manage.py migrate
