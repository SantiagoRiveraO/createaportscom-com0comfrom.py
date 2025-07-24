#!/usr/bin/env python3
"""
Prueba completa del Com0comManager
"""

from com0com_manager import Com0comManager
import time


def main():
    print("🚀 PRUEBA COMPLETA DEL COM0COM MANAGER")
    print("=" * 60)
    
    # Crear manager
    manager = Com0comManager()
    
    # 1. Verificar instalación
    print("\n1️⃣ VERIFICANDO INSTALACIÓN")
    print("-" * 30)
    if manager.is_installed():
        print("✅ Com0com detectado correctamente")
        print(f"📁 Ruta: {manager.com0com_path}")
    else:
        print("❌ Com0com no detectado")
        return
    
    # 2. Listar puertos existentes
    print("\n2️⃣ PUERTOS EXISTENTES")
    print("-" * 30)
    ports = manager.list_ports()
    print(f"📋 Puertos encontrados: {len(ports)}")
    for port in ports:
        print(f"   - {port['name']} ({port['type']})")
    
    # 3. Crear puertos paired
    print("\n3️⃣ CREANDO PUERTOS PAIRED")
    print("-" * 30)
    com1, com2 = "COM20", "COM21"  # Usar puertos menos comunes
    print(f"🔧 Creando par: {com1} ↔ {com2}")
    
    success = manager.create_paired_ports(com1, com2)
    if success:
        print("✅ Puertos creados exitosamente")
        
        # 4. Listar puertos después de la creación
        print("\n4️⃣ PUERTOS DESPUÉS DE LA CREACIÓN")
        print("-" * 30)
        updated_ports = manager.list_ports()
        print(f"📋 Puertos encontrados: {len(updated_ports)}")
        for port in updated_ports:
            print(f"   - {port['name']} ({port['type']})")
        
        # 5. Probar comunicación
        print("\n5️⃣ PRUEBA DE COMUNICACIÓN")
        print("-" * 30)
        print("🔄 Esperando a que los puertos estén listos...")
        time.sleep(3)
        
        comm_success = manager.test_communication(com1, com2)
        if comm_success:
            print("🎉 ¡Comunicación exitosa!")
        else:
            print("⚠️ Problema en la comunicación")
        
        # 6. Limpiar puertos
        print("\n6️⃣ LIMPIEZA")
        print("-" * 30)
        cleanup_success = manager.remove_ports(com1, com2)
        if cleanup_success:
            print("✅ Puertos eliminados correctamente")
        else:
            print("❌ Error al eliminar puertos")
        
        # 7. Verificar limpieza
        print("\n7️⃣ VERIFICACIÓN FINAL")
        print("-" * 30)
        final_ports = manager.list_ports()
        print(f"📋 Puertos restantes: {len(final_ports)}")
        for port in final_ports:
            print(f"   - {port['name']} ({port['type']})")
        
        print("\n" + "=" * 60)
        print("🎉 ¡PRUEBA COMPLETA EXITOSA!")
        print("=" * 60)
        
    else:
        print("❌ Error al crear puertos")
        print("\n" + "=" * 60)
        print("❌ PRUEBA FALLIDA")
        print("=" * 60)


if __name__ == "__main__":
    main() 