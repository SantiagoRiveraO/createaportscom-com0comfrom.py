# Com0com Manager

Un gestor de puertos COM virtuales para Windows que automatiza la creación y configuración de pares de puertos COM usando com0com.

## 🚀 Características

- ✅ **Detección automática** de com0com instalado
- 🔧 **Creación automática** de pares de puertos COM virtuales
- 🔗 **Configuración paired** para comunicación entre puertos
- ⚙️ **Configuración automática** de baudrate a 115200
- 🧪 **Pruebas de comunicación** entre puertos
- 🧹 **Limpieza automática** de puertos creados

## 📋 Requisitos

- Windows 10/11
- Python 3.7+
- com0com instalado ([Descargar aquí](https://sourceforge.net/projects/com0com/))

## 🛠️ Instalación

1. **Instalar com0com:**
   - Descarga e instala com0com desde [SourceForge](https://sourceforge.net/projects/com0com/)
   - Asegúrate de que `setupc.exe` esté disponible en el sistema

2. **Instalar dependencias de Python:**
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Uso

### Uso básico

```python
from com0com_manager import Com0comManager

# Crear manager
manager = Com0comManager()

# Verificar si com0com está instalado
if manager.is_installed():
    print("✅ Com0com encontrado")
    
    # Crear par de puertos
    success = manager.create_paired_ports("COM3", "COM4")
    
    if success:
        # Probar comunicación
        manager.test_communication("COM3", "COM4")
```

### Ejecutar ejemplo completo

```bash
python example.py
```

## 🔧 Funciones principales

### `Com0comManager()`
Constructor que detecta automáticamente la instalación de com0com.

### `is_installed() -> bool`
Verifica si com0com está instalado en el sistema.

### `list_ports() -> List[dict]`
Lista todos los puertos COM configurados actualmente.

### `create_paired_ports(com1: str, com2: str) -> bool`
Crea un par de puertos COM virtuales que se comunican entre sí:
- `com1`: Nombre del primer puerto (ej: "COM3")
- `com2`: Nombre del segundo puerto (ej: "COM4")
- Configura automáticamente baudrate a 115200

### `test_communication(com1: str, com2: str) -> bool`
Prueba la comunicación entre dos puertos COM enviando un mensaje de prueba.

### `remove_ports(com1: str, com2: str) -> bool`
Elimina un par de puertos COM virtuales.

## 📁 Estructura del proyecto

```
CHINO/
├── com0com_manager.py    # Clase principal
├── example.py           # Ejemplo de uso
├── requirements.txt     # Dependencias
└── README.md           # Este archivo
```

## ⚠️ Notas importantes

1. **Permisos de administrador:** Algunas operaciones pueden requerir permisos de administrador
2. **Puertos en uso:** Asegúrate de que los puertos COM no estén siendo utilizados por otras aplicaciones
3. **Com0com instalado:** El sistema debe tener com0com instalado para funcionar

## 🔍 Solución de problemas

### Com0com no encontrado
- Verifica que com0com esté instalado correctamente
- Asegúrate de que `setupc.exe` esté en una de las rutas estándar

### Error al crear puertos
- Verifica que los puertos COM no estén en uso
- Ejecuta como administrador si es necesario
- Revisa que com0com esté funcionando correctamente

### Error de comunicación
- Espera unos segundos después de crear los puertos
- Verifica que no haya otras aplicaciones usando los puertos
- Revisa la configuración de baudrate

## 📝 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT. 