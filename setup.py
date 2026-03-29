# setup.py
import os
import sys
import django
from django.contrib.auth import get_user_model

def create_superuser():
    """Crea superusuario si no existe"""
    User = get_user_model()
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    
    if not password:
        print("⚠️ No se encontró DJANGO_SUPERUSER_PASSWORD, saltando creación de superusuario")
        return
    
    if not User.objects.filter(username=username).exists():
        print(f"🔧 Creando superusuario: {username}")
        User.objects.create_superuser(username=username, email=email, password=password)
        print("✅ Superusuario creado exitosamente")
    else:
        print(f"✅ Superusuario {username} ya existe")

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'htwl.settings')
    django.setup()
    create_superuser()