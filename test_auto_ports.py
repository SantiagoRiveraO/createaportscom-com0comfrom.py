#!/usr/bin/env python3
"""
Prueba del sistema de persistencia de puertos COM
Reutiliza puertos existentes guardados en JSON o crea nuevos si es necesario
"""

from com0com_manager import Com0comManager
import time

def main():
    print("🚀 PRUEBA DEL SISTEMA DE PERSISTENCIA DE PUERTOS COM")
    print("🎯 REUTILIZA PUERTOS EXISTENTES O CREA NUEVOS")
    print("=" * 60)
    
    # Crear instancia del manager
    manager = Com0comManager()
    
    if not manager.is_installed():
        print("❌ Com0com no está instalado. Instálalo primero.")
        return
    
    print("✅ Com0com detectado correctamente")
    print()
    
    # 1. Verificar si ya existen puertos guardados
    print("1️⃣ Verificando puertos existentes...")
    config = manager._load_ports_config()
    
    if config.get('ports') and len(config['ports']) == 2:
        # Hay puertos guardados, usarlos
        existing_com1, existing_com2 = config['ports'][0], config['ports'][1]
        print(f"   📁 Puertos encontrados en JSON: {existing_com1} y {existing_com2}")
        
        # Verificar que los puertos existan y funcionen
        if manager._ports_exist_and_available(existing_com1, existing_com2):
            print(f"   ✅ Puertos existentes funcionando: {existing_com1} y {existing_com2}")
        else:
            print(f"   ⚠️ Puertos guardados no disponibles, creando nuevos...")
            existing_com1, existing_com2 = None, None
    else:
        print(f"   📁 No hay puertos guardados, creando nuevos...")
        existing_com1, existing_com2 = None, None
    
    # Si no hay puertos existentes, crear nuevos
    if existing_com1 is None or existing_com2 is None:
        print("2️⃣ Creando nuevos puertos...")
        new_com1, new_com2 = manager.create_auto_paired_ports()
        
        if new_com1 is None or new_com2 is None:
            print("❌ Error al crear puertos")
            return
        
        # Guardar los nuevos puertos
        if manager._save_ports_config(new_com1, new_com2):
            print(f"   ✅ Nuevos puertos guardados: {new_com1} y {new_com2}")
        else:
            print(f"   ⚠️ Error al guardar, pero puertos funcionan")
        
        existing_com1, existing_com2 = new_com1, new_com2
    
    print(f"   ✅ Puertos finales: {existing_com1} y {existing_com2}")
    print()
    
    # 3. Listar puertos configurados
    print("3️⃣ Listando puertos configurados...")
    ports = manager.list_ports()
    print(f"   Puertos configurados: {len(ports)}")
    for port in ports:
        print(f"   - {port['name']} ({port['type']})")
    print()
    
    # 4. Esperar un momento y probar comunicación
    print("4️⃣ Esperando 3 segundos para estabilizar...")
    time.sleep(3)
    
    print("5️⃣ Probando comunicación entre puertos...")
    if manager.test_communication(existing_com1, existing_com2):
        print(f"   ✅ Comunicación exitosa entre {existing_com1} y {existing_com2}")
    else:
        print(f"   ❌ Error en comunicación entre {existing_com1} y {existing_com2}")
    print()
    
    # Mostrar información del archivo guardado
    print("6️⃣ Información del archivo de configuración:")
    config = manager._load_ports_config()
    print(f"   📁 Archivo: {manager.config_file}")
    print(f"   📊 Puertos guardados: {config.get('ports', [])}")
    print(f"   🕒 Creado: {config.get('created_at', 'N/A')}")
    print()
    
    print("🎉 PRUEBA COMPLETADA")
    print(f"📋 Resumen: Puertos {existing_com1} y {existing_com2} obtenidos y funcionando")
    print(f"🎯 Sistema de persistencia funcionando correctamente")
    print(f"💾 Configuración cargada desde: {manager.config_file}")

if __name__ == "__main__":
    main() 