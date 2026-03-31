#!/usr/bin/env python
"""
Script para visualizar la estructura de archivos Python y HTML del proyecto
Ejecutar: python show_structure.py
"""

import os
from pathlib import Path

# Directorios a ignorar
IGNORE_DIRS = {
    '__pycache__', '.git', '.vscode', 'idea', 
    'venv', 'env', 'envs', 'virtualenv',
    'node_modules', 'migrations', 'staticfiles', 'media'
}

def should_ignore_dir(name):
    """Determinar si un directorio debe ser ignorado"""
    if name in IGNORE_DIRS:
        return True
    if name.startswith('.'):
        return True
    return False

def is_relevant_file(filename):
    """Verificar si es un archivo .py o .html"""
    return filename.endswith('.py') or filename.endswith('.html')

def print_tree(directory, prefix="", is_last=True, level=0, max_depth=5):
    """
    Imprime la estructura de directorios mostrando solo .py y .html
    """
    if level > max_depth:
        return
    
    try:
        items = list(Path(directory).iterdir())
    except PermissionError:
        return
    
    # Filtrar solo directorios relevantes y archivos .py/.html
    dirs = []
    files = []
    
    for item in items:
        if item.is_dir():
            if not should_ignore_dir(item.name):
                dirs.append(item)
        else:
            if is_relevant_file(item.name):
                files.append(item)
    
    # Ordenar
    dirs.sort(key=lambda x: x.name.lower())
    files.sort(key=lambda x: x.name.lower())
    
    # Combinar directorios primero, luego archivos
    all_items = dirs + files
    
    for i, item in enumerate(all_items):
        is_last_item = (i == len(all_items) - 1)
        current_prefix = "└── " if is_last_item else "├── "
        
        if item.is_dir():
            print(f"{prefix}{current_prefix}📁 {item.name}/")
            next_prefix = prefix + ("    " if is_last_item else "│   ")
            print_tree(item, next_prefix, is_last_item, level + 1, max_depth)
        else:
            # Mostrar archivo con su extensión
            ext = "🐍" if item.name.endswith('.py') else "🌐"
            print(f"{prefix}{current_prefix}{ext} {item.name}")

def main():
    """Función principal"""
    print("\n" + "="*70)
    print("📁 ESTRUCTURA DEL PROYECTO DJANGO")
    print("="*70)
    print("🐍 = Archivo Python | 🌐 = Archivo HTML")
    print("-"*70)
    
    # Directorio actual (donde está manage.py)
    base_dir = Path.cwd()
    
    # Buscar manage.py para confirmar que estamos en el proyecto
    manage_py = base_dir / 'manage.py'
    if not manage_py.exists():
        print("⚠️  No se encontró manage.py. Asegúrate de ejecutar este script en la raíz del proyecto.")
        return
    
    print(f"\n📂 {base_dir.name}/")
    print_tree(base_dir)
    
    print("\n" + "="*70)
    print("✅ Estructura generada correctamente")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()