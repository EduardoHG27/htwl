#!/usr/bin/env python
import os
import sys
import time
import django
from django.db import connections
from django.db.utils import OperationalError

def wait_for_db():
    print("⏳ Esperando a que PostgreSQL esté lista...")
    db_conn = None
    max_retries = 30
    retry_count = 0
    
    while not db_conn and retry_count < max_retries:
        try:
            connections['default'].cursor()
            db_conn = True
            print("✅ Base de datos conectada!")
        except OperationalError:
            print(f"⚠️ Base de datos no disponible, reintentando... (intento {retry_count + 1}/{max_retries})")
            time.sleep(1)
            retry_count += 1
    
    if not db_conn:
        print("❌ No se pudo conectar a la base de datos")
        sys.exit(1)

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'htwl.settings')
    django.setup()
    wait_for_db()
    print("🔄 Ejecutando migraciones...")
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'migrate'])
    print("✅ Migraciones completadas!")