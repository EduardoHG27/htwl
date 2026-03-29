import os
import sys
from pathlib import Path

def mostrar_estructura(directorio, nivel=0, max_nivel=3, ignorar_dirs=None):
    """
    Muestra la estructura de carpetas y archivos
    """
    if ignorar_dirs is None:
        ignorar_dirs = ['.git', '__pycache__', 'node_modules', '.venv', 'venv', 
                       '.env', 'dist', 'build', '.pytest_cache', '.coverage']
    
    if nivel > max_nivel:
        return
    
    try:
        items = sorted(os.listdir(directorio))
        
        for item in items:
            # Ignorar archivos/directorios ocultos
            if item.startswith('.') and item not in ['.env.example', '.gitignore']:
                continue
            if item in ignorar_dirs:
                continue
                
            ruta_completa = os.path.join(directorio, item)
            indentacion = "  " * nivel
            
            if os.path.isdir(ruta_completa):
                print(f"{indentacion}📁 {item}/")
                mostrar_estructura(ruta_completa, nivel + 1, max_nivel, ignorar_dirs)
            else:
                # Obtener tamaño del archivo
                try:
                    tamaño = os.path.getsize(ruta_completa)
                    if tamaño < 1024:
                        tamaño_str = f"{tamaño} B"
                    elif tamaño < 1024 * 1024:
                        tamaño_str = f"{tamaño/1024:.1f} KB"
                    else:
                        tamaño_str = f"{tamaño/(1024*1024):.1f} MB"
                except:
                    tamaño_str = "? B"
                    
                print(f"{indentacion}📄 {item} ({tamaño_str})")
                
    except PermissionError:
        print(f"{'  ' * nivel}⚠️ Permiso denegado")

def identificar_tipo_proyecto(directorio):
    """Identifica el tipo de proyecto por los archivos presentes"""
    archivos = os.listdir(directorio)
    
    if 'requirements.txt' in archivos:
        return 'Python (pip)'
    elif 'package.json' in archivos:
        return 'Node.js'
    elif 'manage.py' in archivos:
        return 'Django (Python)'
    elif 'app.py' in archivos or 'main.py' in archivos:
        return 'Python (Flask/FastAPI)'
    elif 'pom.xml' in archivos:
        return 'Java (Maven)'
    else:
        return 'Desconocido'

def encontrar_archivos_clave(directorio):
    """Encuentra archivos importantes para Railway"""
    archivos = os.listdir(directorio)
    clave = {
        'entrada': None,
        'config': [],
        'docker': None
    }
    
    # Buscar archivos de entrada comunes
    entradas_comunes = ['manage.py', 'app.py', 'main.py', 'server.py', 'wsgi.py', 'index.js', 'server.js']
    for entrada in entradas_comunes:
        if entrada in archivos:
            clave['entrada'] = entrada
            break
    
    # Buscar archivos de configuración
    configs = ['requirements.txt', 'package.json', 'Dockerfile', 'docker-compose.yml', '.env.example']
    for config in configs:
        if config in archivos:
            clave['config'].append(config)
    
    # Verificar Dockerfile específicamente
    if 'Dockerfile' in archivos:
        clave['docker'] = 'Dockerfile'
    
    return clave

def main():
    # Obtener el directorio a analizar
    if len(sys.argv) > 1:
        ruta_base = sys.argv[1]
    else:
        ruta_base = os.getcwd()
    
    if not os.path.exists(ruta_base):
        print(f"❌ Error: La ruta '{ruta_base}' no existe")
        return
    
    print("\n" + "="*60)
    print("📊 ANÁLISIS DE PROYECTO PARA RAILWAY")
    print("="*60)
    
    # Información básica
    print(f"\n📁 Proyecto: {os.path.basename(ruta_base)}")
    print(f"📍 Ruta: {ruta_base}")
    print(f"🔧 Tipo: {identificar_tipo_proyecto(ruta_base)}")
    
    # Archivos clave
    clave = encontrar_archivos_clave(ruta_base)
    print(f"\n🔑 Archivos clave encontrados:")
    if clave['entrada']:
        print(f"   • Archivo de entrada: {clave['entrada']}")
    if clave['config']:
        print(f"   • Configuración: {', '.join(clave['config'])}")
    if clave['docker']:
        print(f"   • Docker: {clave['docker']}")
    
    # Estructura del proyecto
    print(f"\n📂 ESTRUCTURA DEL PROYECTO:")
    print(f"📂 {os.path.basename(ruta_base)}/")
    mostrar_estructura(ruta_base, nivel=1, max_nivel=3)
    
    # Recomendaciones para Railway
    print(f"\n🚂 RECOMENDACIONES PARA RAILWAY:")
    
    tipo = identificar_tipo_proyecto(ruta_base)
    
    if tipo == 'Django (Python)':
        print("   ✅ Proyecto Django detectado")
        print("   📝 Archivo de entrada: manage.py")
        print("   💡 Para Railway, necesitarás:")
        print("      • requirements.txt con todas las dependencias")
        print("      • Archivo runtime.txt con la versión de Python (ej: python-3.11.0)")
        print("      • Variables de entorno:")
        print("         - SECRET_KEY (clave secreta de Django)")
        print("         - DEBUG (False en producción)")
        print("         - ALLOWED_HOSTS (tu dominio en Railway)")
        print("         - DATABASE_URL (si usas base de datos)")
        
        # Verificar si existe requirements.txt
        if 'requirements.txt' not in clave['config']:
            print("   ⚠️  No se encontró requirements.txt - Debes crearlo con:")
            print("      pip freeze > requirements.txt")
    
    elif tipo == 'Python (pip)':
        print("   ✅ Proyecto Python detectado")
        if clave['entrada']:
            print(f"   📝 Archivo de entrada: {clave['entrada']}")
        if 'requirements.txt' in clave['config']:
            print("   ✅ requirements.txt encontrado")
        else:
            print("   ⚠️  No se encontró requirements.txt - Crea uno con tus dependencias")
    
    elif tipo == 'Node.js':
        print("   ✅ Proyecto Node.js detectado")
        print("   📝 Railway ejecutará: npm start")
        print("   💡 Asegúrate de tener 'start' script en package.json")
    
    else:
        print("   ℹ️  Tipo de proyecto no detectado automáticamente")
        print("   💡 Recomendaciones generales:")
        print("      • Asegúrate de tener un archivo de entrada principal")
        print("      • Define las dependencias en requirements.txt o package.json")
        print("      • Configura las variables de entorno necesarias")
    
    print("\n" + "="*60)
    print("\n📌 PRÓXIMOS PASOS:")
    print("1. Asegúrate de tener requirements.txt con todas las dependencias")
    print("2. Configura las variables de entorno en Railway")
    print("3. Define el comando de inicio en Railway")
    print("4. Si usas base de datos, configura DATABASE_URL")
    print("="*60)

if __name__ == "__main__":
    main()