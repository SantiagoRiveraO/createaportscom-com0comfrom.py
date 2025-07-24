#!/usr/bin/env python3
"""
Prueba completa de creación y configuración de puertos
"""

import os
import subprocess
import sys
import time

def find_setupc():
    """Encuentra setupc.exe"""
    possible_paths = [
        r"C:\Program Files\com0com\setupc.exe",
        r"C:\Program Files (x86)\com0com\setupc.exe",
        r"C:\com0com\setupc.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def main():
    print("🔧 PRUEBA COMPLETA DE CREACIÓN Y CONFIGURACIÓN")
    print("=" * 50)
    
    setupc_path = find_setupc()
    if not setupc_path:
        print("❌ setupc.exe no encontrado")
        return
    
    com0com_dir = os.path.dirname(setupc_path)
    print(f"✅ setupc.exe encontrado en: {setupc_path}")
    print(f"📁 Directorio com0com: {com0com_dir}")
    print()
    
    # Probar install con directorio de trabajo correcto
    print("1️⃣ Creando par de puertos COM20 y COM21...")
    try:
        result = subprocess.run([setupc_path, "install", "PortName=COM20", "PortName=COM21"], 
                              capture_output=True, text=True, timeout=10, cwd=com0com_dir)
        print(f"   Salida: {result.stdout.strip()}")
        print(f"   Error: {result.stderr.strip()}")
        print(f"   Código: {result.returncode}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Configurar baudrate y otros parámetros
    print("2️⃣ Configurando baudrate y parámetros...")
    try:
        # Configurar CNCA1 (COM20)
        result = subprocess.run([setupc_path, "change", "CNCA1", "EmuBR=yes"], 
                              capture_output=True, text=True, timeout=10, cwd=com0com_dir)
        print(f"   CNCA1 EmuBR=yes: {result.stdout.strip()}")
        print(f"   Código: {result.returncode}")
        
        # Configurar CNCB1 (COM21)
        result = subprocess.run([setupc_path, "change", "CNCB1", "EmuBR=yes"], 
                              capture_output=True, text=True, timeout=10, cwd=com0com_dir)
        print(f"   CNCB1 EmuBR=yes: {result.stdout.strip()}")
        print(f"   Código: {result.returncode}")
        
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Listar puertos después de configurar
    print("3️⃣ Listando puertos después de configurar...")
    try:
        result = subprocess.run([setupc_path, "list"], 
                              capture_output=True, text=True, timeout=10, cwd=com0com_dir)
        print(f"   Salida: {result.stdout.strip()}")
        print(f"   Error: {result.stderr.strip()}")
        print(f"   Código: {result.returncode}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Esperar un momento para que los cambios se apliquen
    print("4️⃣ Esperando 2 segundos para que los cambios se apliquen...")
    time.sleep(2)
    print("   ✅ Listo!")
    print()

if __name__ == "__main__":
    main() 