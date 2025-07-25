# 🔧 CHINO - Gestor de Puertos COM Virtuales

Una aplicación completa de escritorio para la gestión y escucha de puertos COM virtuales usando Com0com.

## 🚀 Características

### ✅ **Gestión Automática de Com0com**
- Verificación automática de instalación de Com0com
- Enlace directo de descarga si no está instalado
- Configuración automática de puertos virtuales

### ✅ **Creación Inteligente de Puertos**
- Detección automática de puertos disponibles
- Creación de pares de puertos consecutivos
- Configuración automática con "Use Ports Class" activado
- Baudrate configurado a 115200
- Emulación de baudrate desactivada

### ✅ **Sistema de Persistencia**
- Guardado automático de configuración en JSON
- Reutilización de puertos existentes
- No crea puertos duplicados innecesariamente

### ✅ **Interfaz de Escucha en Tiempo Real**
- Escucha de JSONs desde puertos COM
- Parsing inteligente de JSONs completos
- Contador de mensajes recibidos
- Interfaz moderna con pestañas

## 📋 Requisitos

- **Windows 10/11** (64-bit)
- **Python 3.7+**
- **Com0com** (se descarga automáticamente si no está instalado)

## 🛠️ Instalación

### 1. Clonar o Descargar
```bash
git clone <repository-url>
cd CHINO
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar la Aplicación
```bash
# Opción 1: Usando el archivo batch
run_chino.bat

# Opción 2: Directamente con Python
python main_app.py
```

## 🎯 Uso

### **Primera Ejecución**
1. La aplicación verifica automáticamente si Com0com está instalado
2. Si no está instalado, muestra un botón para descargarlo
3. Después de instalar Com0com, vuelve a la aplicación

### **Crear Puertos COM**
1. Haz clic en "🔧 Crear Puertos COM"
2. La aplicación crea automáticamente un par de puertos consecutivos
3. Los puertos se configuran con los parámetros óptimos
4. La configuración se guarda automáticamente

### **Escuchar JSONs**
1. Ve a la pestaña "🔍 Escucha de Puertos"
2. Selecciona uno de los puertos creados
3. Haz clic en "🔌 Conectar"
4. Los JSONs recibidos aparecen en tiempo real

## 📁 Estructura del Proyecto

```
CHINO/
├── main_app.py              # Aplicación principal
├── com0com_manager.py       # Gestor de Com0com
├── com_listener.py          # Interfaz de escucha (legacy)
├── test_auto_ports.py       # Script de prueba
├── requirements.txt         # Dependencias Python
├── com_ports_config.json    # Configuración guardada
├── run_chino.bat           # Ejecutor principal
├── run_auto_test.bat       # Ejecutor de pruebas
├── run_listener.bat        # Ejecutor de escucha (legacy)
└── README.md               # Este archivo
```

## ⚙️ Configuración

### **Parámetros de Puertos**
- **Baudrate:** 115200
- **Use Ports Class:** Activado
- **Emulación de Baudrate:** Desactivada
- **Configuración:** Guardada en `com_ports_config.json`

### **Archivo de Configuración**
```json
{
  "ports": ["COM13", "COM14"],
  "created_at": "2025-07-24 18:45:32"
}
```

## 🔧 Funcionalidades Técnicas

### **Detección de Com0com**
- Busca en rutas estándar de instalación
- Verifica existencia de `setupc.exe`
- Soporte para instalaciones personalizadas

### **Gestión de Puertos**
- Detección automática de puertos ocupados
- Búsqueda de pares consecutivos disponibles
- Creación programática usando `setupc.exe`
- Configuración automática de parámetros

### **Escucha de Datos**
- Thread separado para no bloquear la interfaz
- Parsing inteligente de JSONs completos
- Manejo de JSONs fragmentados
- Timestamps precisos de recepción

## 🐛 Solución de Problemas

### **Error: "Com0com no está instalado"**
- Descarga Com0com usando el botón en la aplicación
- Instala como administrador
- Reinicia la aplicación

### **Error: "Access denied" al crear puertos**
- Ejecuta la aplicación como administrador
- Verifica que Com0com esté instalado correctamente

### **Error: "No se pueden crear puertos"**
- Verifica que haya puertos COM disponibles
- Cierra otras aplicaciones que usen puertos COM
- Reinicia la aplicación

### **Error: "No se puede conectar al puerto"**
- Verifica que el puerto no esté en uso
- Asegúrate de que el puerto esté creado
- Revisa la configuración de baudrate

## 📝 Logs y Debugging

La aplicación muestra logs detallados en tiempo real:
- Estado de verificación de Com0com
- Proceso de creación de puertos
- Errores y advertencias
- Mensajes recibidos con timestamps

## 🔄 Actualizaciones

### **Versión 1.0**
- ✅ Gestión completa de Com0com
- ✅ Creación automática de puertos
- ✅ Sistema de persistencia
- ✅ Interfaz de escucha en tiempo real
- ✅ Interfaz moderna con pestañas

## 📞 Soporte

Para reportar problemas o solicitar características:
1. Revisa la sección de solución de problemas
2. Verifica los logs de la aplicación
3. Asegúrate de cumplir los requisitos del sistema

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver archivo LICENSE para más detalles.

---

**CHINO** - Simplificando la gestión de puertos COM virtuales 🚀
