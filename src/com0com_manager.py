import os
import subprocess
import time
import winreg
import json
import logging
import ctypes
from typing import Tuple, Optional, List
import serial

# Configurar sistema de logging
def setup_logging():
    """Configura el sistema de logging para la aplicación"""
    # Crear directorio de logs si no existe
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar formato de logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configurar logging para archivo
    file_handler = logging.FileHandler(os.path.join(log_dir, 'com0com_manager.log'), encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Configurar logging para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    
    # Configurar logger principal
    logger = logging.getLogger('Com0comManager')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Crear logger global
logger = setup_logging()

def is_admin():
    """
    Verifica si la aplicación tiene permisos de administrador
    Returns:
        bool: True si tiene permisos de administrador, False en caso contrario
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def require_admin_privileges():
    """
    Verifica que la aplicación tenga permisos de administrador
    Si no los tiene, muestra un error y termina la aplicación
    """
    if not is_admin():
        logger.critical("❌ PERMISOS DE ADMINISTRADOR REQUERIDOS")
        logger.critical("Esta aplicación necesita permisos de administrador para:")
        logger.critical("• Crear puertos COM virtuales")
        logger.critical("• Modificar configuraciones del sistema")
        logger.critical("• Acceder a drivers de com0com")
        
        # Mostrar mensaje de error
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana principal
        
        error_message = """❌ PERMISOS DE ADMINISTRADOR REQUERIDOS

Esta aplicación necesita permisos de administrador para funcionar correctamente.

¿Por qué se necesitan permisos de administrador?
• Crear puertos COM virtuales
• Modificar configuraciones del sistema
• Acceder a drivers de com0com

SOLUCIÓN:
Ejecuta la aplicación usando 'run_chino_admin.bat' que solicitará permisos automáticamente.

La aplicación se cerrará ahora."""
        
        messagebox.showerror("Permisos de Administrador Requeridos", error_message)
        root.destroy()
        
        # Terminar la aplicación
        import sys
        sys.exit(1)
    
    logger.info("✅ Permisos de administrador verificados correctamente")


class Com0comManager:
    """
    Clase para gestionar puertos COM virtuales usando com0com
    """
    
    def __init__(self, config_file="config/com_ports_config.json"):
        # Verificar permisos de administrador ANTES de cualquier operación
        require_admin_privileges()
        
        self.com0com_path = None
        self.setupc_path = None
        self.config_file = config_file
        logger.info("🔧 Inicializando Com0comManager")
        self._find_com0com_installation()
    
    def _find_com0com_installation(self) -> bool:
        """
        Detecta si com0com está instalado y encuentra las rutas necesarias
        """
        logger.info("🔍 Buscando instalación de Com0com...")
        
        # Rutas comunes donde se instala com0com
        possible_paths = [
            r"C:\Program Files\com0com\setupc.exe",
            r"C:\Program Files (x86)\com0com\setupc.exe",
            r"C:\com0com\setupc.exe",
            os.path.join(os.getcwd(), "com0com", "setupc.exe")  # Buscar en carpeta local
        ]
        
        # Buscar en el registro de Windows
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\com0com") as key:
                install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                possible_paths.insert(0, os.path.join(install_path, "setupc.exe"))
                logger.debug(f"📋 Com0com encontrado en registro: {install_path}")
        except (FileNotFoundError, OSError) as e:
            logger.debug(f"📋 Com0com no encontrado en registro: {e}")
        
        # Verificar si existe setupc.exe en alguna de las rutas
        for path in possible_paths:
            if os.path.exists(path):
                self.setupc_path = path
                self.com0com_path = os.path.dirname(path)
                logger.info(f"✅ Com0com encontrado en: {self.com0com_path}")
                return True
        
        logger.error("❌ Com0com no encontrado. Por favor instálalo desde: https://sourceforge.net/projects/com0com/")
        return False
    
    def _load_ports_config(self) -> dict:
        """
        Carga la configuración de puertos desde el archivo
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Error al cargar configuración: {e}")
        return {"ports": [], "created_at": None}
    
    def _save_ports_config(self, com1: str, com2: str) -> bool:
        """
        Guarda la configuración de puertos en el archivo
        """
        try:
            config = {
                "ports": [com1, com2],
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Obtener ruta absoluta del archivo
            abs_path = os.path.abspath(self.config_file)
            logger.info(f"💾 Guardando configuración en: {abs_path}")
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Verificar que el archivo se creó
            if os.path.exists(self.config_file):
                logger.info(f"✅ Archivo creado exitosamente: {com1} y {com2}")
                logger.info(f"📁 Ubicación: {abs_path}")
                return True
            else:
                logger.error(f"❌ Error: El archivo no se creó en {abs_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error al guardar configuración: {e}")
            logger.warning(f"📁 Intentando guardar en: {os.path.abspath(self.config_file)}")
            return False
    
    def _check_existing_ports(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Verifica si ya existen puertos configurados y si están disponibles
        """
        config = self._load_ports_config()
        
        if not config.get("ports") or len(config["ports"]) < 2:
            return None, None
        
        com1, com2 = config["ports"][0], config["ports"][1]
        logger.info(f"🔍 Verificando puertos existentes: {com1} y {com2}")
        
        # Verificar si los puertos están realmente disponibles
        if self._ports_exist_and_available(com1, com2):
            logger.info(f"✅ Puertos existentes encontrados y disponibles: {com1} y {com2}")
            return com1, com2
        else:
            logger.warning(f"❌ Puertos existentes no están disponibles, se crearán nuevos")
            return None, None
    
    def _ports_exist_in_com0com(self, com1: str, com2: str) -> bool:
        """
        Verifica si los puertos existen en com0com (sin probar comunicación)
        """
        try:
            # Verificar si los puertos están en la lista de com0com
            result = subprocess.run([self.setupc_path, "list"], 
                                  capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
            
            # Buscar si ambos puertos están en la lista
            lines = result.stdout.split('\n')
            com1_found = False
            com2_found = False
            
            for line in lines:
                if com1 in line and 'CNCA' in line:
                    com1_found = True
                elif com2 in line and 'CNCB' in line:
                    com2_found = True
            
            return com1_found and com2_found
            
        except Exception as e:
            logger.warning(f"⚠️ Error al verificar puertos en com0com: {e}")
            return False

    def _ports_exist_and_available(self, com1: str, com2: str) -> bool:
        """
        Verifica si los puertos existen y están disponibles para comunicación
        """
        try:
            # Verificar que existan en com0com
            if not self._ports_exist_in_com0com(com1, com2):
                return False
            
            # Probar comunicación básica
            return self.test_communication(com1, com2)
            
        except Exception as e:
            logger.warning(f"⚠️ Error al verificar puertos: {e}")
            return False
    
    def get_or_create_paired_ports(self) -> Tuple[str, str]:
        """
        Obtiene puertos existentes o crea nuevos si es necesario
        
        Returns:
            Tuple[str, str]: Par de puertos disponibles
        """
        logger.info("🔍 Verificando puertos existentes...")
        
        # Verificar si ya existen puertos configurados
        existing_com1, existing_com2 = self._check_existing_ports()
        
        if existing_com1 and existing_com2:
            logger.info(f"✅ Reutilizando puertos existentes: {existing_com1} y {existing_com2}")
            return existing_com1, existing_com2
        
        # Si no existen, crear nuevos
        logger.info("🆕 Creando nuevos puertos...")
        new_com1, new_com2 = self.create_auto_paired_ports()
        
        if new_com1 and new_com2:
            # Guardar la nueva configuración
            logger.info(f"💾 Guardando configuración de puertos nuevos...")
            save_success = self._save_ports_config(new_com1, new_com2)
            if save_success:
                logger.info(f"✅ Configuración guardada correctamente")
            else:
                logger.warning(f"⚠️ Error al guardar configuración, pero los puertos funcionan")
            return new_com1, new_com2
        else:
            logger.error("❌ Error al crear nuevos puertos")
            return None, None
    
    def clear_ports_config(self) -> bool:
        """
        Limpia la configuración guardada de puertos
        """
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                logger.info(f"🗑️ Configuración eliminada: {self.config_file}")
                return True
        except Exception as e:
            logger.error(f"❌ Error al eliminar configuración: {e}")
        return False
    
    def is_installed(self) -> bool:
        """
        Verifica si com0com está instalado
        """
        return self.setupc_path is not None and os.path.exists(self.setupc_path)
    
    def list_ports(self) -> List[dict]:
        """
        Lista todos los puertos COM configurados
        """
        if not self.is_installed():
            return []
        
        try:
            result = subprocess.run([self.setupc_path, "list"], 
                                  capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
            
            ports = []
            for line in result.stdout.split('\n'):
                if 'COM' in line and 'CNCA' in line:
                    # Parsear línea como: COM3 - CNCA0
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        port_name = parts[0]
                        port_type = parts[2]
                        ports.append({
                            'name': port_name,
                            'type': port_type,
                            'status': 'active'
                        })
            
            return ports
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Timeout al listar puertos")
            return []
        except Exception as e:
            logger.error(f"❌ Error al listar puertos: {e}")
            return []
    
    def get_available_com_ports(self) -> List[str]:
        """
        Obtiene una lista de puertos COM disponibles (no ocupados)
        """
        if not self.is_installed():
            return []
        
        try:
            # Usar setupc.exe para ver puertos ocupados
            result = subprocess.run([self.setupc_path, "busynames", "COM*"], 
                                  capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
            
            busy_ports = []
            for line in result.stdout.split('\n'):
                if 'COM' in line:
                    # Extraer número de puerto ocupado
                    parts = line.strip().split()
                    for part in parts:
                        if part.startswith('COM'):
                            busy_ports.append(part)
            
            # Generar lista de puertos disponibles (COM1 a COM50)
            all_ports = [f"COM{i}" for i in range(1, 51)]
            available_ports = [port for port in all_ports if port not in busy_ports]
            
            logger.info(f"📊 Puertos ocupados: {busy_ports}")
            logger.info(f"📊 Puertos disponibles: {available_ports[:10]}...")  # Mostrar solo los primeros 10
            
            return available_ports
            
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Timeout al verificar puertos disponibles")
            return []
        except Exception as e:
            logger.error(f"❌ Error al verificar puertos disponibles: {e}")
            return []
    
    def find_available_pair(self) -> Tuple[str, str]:
        """
        Encuentra el primer par de puertos COM disponibles consecutivos
        
        Returns:
            Tuple[str, str]: Par de puertos disponibles (ej: ("COM20", "COM21"))
        """
        available_ports = self.get_available_com_ports()
        
        if len(available_ports) < 2:
            logger.error("❌ No hay suficientes puertos COM disponibles")
            return None, None
        
        # Buscar dos puertos consecutivos disponibles
        for i in range(len(available_ports) - 1):
            port1 = available_ports[i]
            port2 = available_ports[i + 1]
            
            # Verificar que sean consecutivos (ej: COM20, COM21)
            try:
                num1 = int(port1[3:])  # Extraer número de COM20 -> 20
                num2 = int(port2[3:])  # Extraer número de COM21 -> 21
                
                if num2 == num1 + 1:
                    logger.info(f"✅ Par disponible encontrado: {port1} y {port2}")
                    return port1, port2
            except ValueError:
                continue
        
        logger.error("❌ No se encontró un par de puertos consecutivos disponibles")
        return None, None
    
    def create_paired_ports(self, com1: str, com2: str) -> bool:
        """
        Crea un par de puertos COM virtuales que se comunican entre sí
        
        Args:
            com1: Nombre del primer puerto (ej: "COM3")
            com2: Nombre del segundo puerto (ej: "COM4")
        
        Returns:
            bool: True si se crearon exitosamente, False en caso contrario
        """
        if not self.is_installed():
            logger.error("❌ Com0com no está instalado")
            return False
        
        try:
            # Crear un par de puertos conectados usando el comando correcto
            # Usar el directorio de com0com como directorio de trabajo
            logger.info(f"🔧 Creando par de puertos {com1} y {com2}...")
            # Usar PortName=COM# para activar automáticamente "use Ports class"
            # Agregar --silent para suprimir diálogos
            result = subprocess.run([self.setupc_path, "--silent", "install", "PortName=COM#", "PortName=COM#"], 
                                   capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
            logger.info(f"   Resultado: {result.stdout.strip()}")
            if result.returncode != 0:
                logger.error(f"   Error: {result.stderr.strip()}")
                return False
            
            # Asignar nombres específicos a los puertos creados
            logger.info(f"🔧 Asignando nombres específicos {com1} y {com2}...")
            list_result = subprocess.run([self.setupc_path, "list"], 
                                       capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
            
            # Buscar los puertos recién creados (CNCA y CNCB del último par)
            lines = list_result.stdout.split('\n')
            cnca_id = None
            cncb_id = None
            
            for line in lines:
                if 'CNCA' in line and 'COM#' in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith('CNCA'):
                            cnca_id = part
                            break
                elif 'CNCB' in line and 'COM#' in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith('CNCB'):
                            cncb_id = part
                            break
            
            if cnca_id and cncb_id:
                try:
                    # Asignar nombres específicos con timeout más largo
                    logger.info(f"   Asignando {cnca_id} -> {com1}...")
                    result2 = subprocess.run([self.setupc_path, "--silent", "change", cnca_id, f"RealPortName={com1}"], 
                                           capture_output=True, text=True, timeout=30, cwd=self.com0com_path)
                    logger.info(f"   {cnca_id} -> {com1}: {result2.stdout.strip()}")
                    
                    logger.info(f"   Asignando {cncb_id} -> {com2}...")
                    result3 = subprocess.run([self.setupc_path, "--silent", "change", cncb_id, f"RealPortName={com2}"], 
                                           capture_output=True, text=True, timeout=30, cwd=self.com0com_path)
                    logger.info(f"   {cncb_id} -> {com2}: {result3.stdout.strip()}")
                    
                    # Esperar un momento para que los cambios se apliquen
                    time.sleep(1)
                except subprocess.TimeoutExpired:
                    logger.warning(f"   ⚠️ Timeout al asignar nombres específicos, pero los puertos se crearon correctamente")
                    logger.info(f"   Los puertos están disponibles como COM# y funcionarán normalmente")
                except Exception as e:
                    logger.warning(f"   ⚠️ Error al asignar nombres específicos: {e}")
                    logger.info(f"   Los puertos se crearon pero mantienen nombres genéricos")
            else:
                logger.warning(f"   ⚠️ No se pudieron encontrar los puertos recién creados")
            
            logger.info(f"⚙️ Configurando parámetros de comunicación...")
            
            # Encontrar los identificadores CNCA y CNCB del par creado
            list_result = subprocess.run([self.setupc_path, "list"], 
                                       capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
            
            # Buscar el par que contiene com1 y com2, o los puertos COM# si no se asignaron nombres específicos
            lines = list_result.stdout.split('\n')
            cnca_id = None
            cncb_id = None
            
            for line in lines:
                if ('CNCA' in line and (com1 in line or 'COM#' in line)):
                    parts = line.split()
                    for part in parts:
                        if part.startswith('CNCA'):
                            cnca_id = part
                            break
                elif ('CNCB' in line and (com2 in line or 'COM#' in line)):
                    parts = line.split()
                    for part in parts:
                        if part.startswith('CNCB'):
                            cncb_id = part
                            break
            
            if cnca_id and cncb_id:
                # Configurar ambos puertos sin emulación de baudrate
                logger.info(f"   Configurando {cnca_id}...")
                result4 = subprocess.run([self.setupc_path, "--silent", "change", cnca_id, "EmuBR=no"], 
                                       capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
                logger.info(f"   {cnca_id} EmuBR=no: {result4.stdout.strip()}")
                
                logger.info(f"   Configurando {cncb_id}...")
                result5 = subprocess.run([self.setupc_path, "--silent", "change", cncb_id, "EmuBR=no"], 
                                       capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
                logger.info(f"   {cncb_id} EmuBR=no: {result5.stdout.strip()}")
                
                logger.info(f"   ✅ Ambos puertos configurados sin emulación de baudrate")
            else:
                logger.warning(f"   ⚠️ No se pudieron encontrar los identificadores CNCA/CNCB")
            
            # Esperar un momento para que los cambios se apliquen
            time.sleep(2)
            
            logger.info(f"✅ Puertos creados y configurados exitosamente")
            return True
            
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Timeout al crear puertos")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return False
    
    def create_auto_paired_ports(self) -> Tuple[str, str]:
        """
        Crea automáticamente un par de puertos COM en las primeras posiciones disponibles
        
        Returns:
            Tuple[str, str]: Par de puertos creados (ej: ("COM20", "COM21")) o (None, None) si falla
        """
        logger.info("🔍 Buscando par de puertos disponibles...")
        com1, com2 = self.find_available_pair()
        
        if com1 is None or com2 is None:
            logger.error("❌ No se pudo encontrar un par de puertos disponibles")
            return None, None
        
        logger.info(f"🎯 Creando par automático en {com1} y {com2}...")
        success = self.create_paired_ports(com1, com2)
        
        if success:
            # Verificar si los nombres específicos se asignaron correctamente
            list_result = subprocess.run([self.setupc_path, "list"], 
                                       capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
            
            # Buscar si los puertos tienen nombres específicos o genéricos
            lines = list_result.stdout.split('\n')
            final_com1 = com1
            final_com2 = com2
            
            for line in lines:
                if com1 in line and 'CNCA' in line:
                    final_com1 = com1
                    break
                elif 'COM#' in line and 'CNCA' in line:
                    # Si no se asignó nombre específico, usar el genérico
                    final_com1 = "COM# (primer puerto del par)"
                    break
            
            for line in lines:
                if com2 in line and 'CNCB' in line:
                    final_com2 = com2
                    break
                elif 'COM#' in line and 'CNCB' in line:
                    # Si no se asignó nombre específico, usar el genérico
                    final_com2 = "COM# (segundo puerto del par)"
                    break
            
            logger.info(f"✅ Par automático creado exitosamente")
            logger.info(f"   Puertos: {final_com1} y {final_com2}")
            return com1, com2  # Retornar los nombres originales para compatibilidad
        else:
            logger.error(f"❌ Error al crear par automático")
            return None, None
    
    def remove_ports(self, com1: str, com2: str) -> bool:
        """
        Elimina un par de puertos COM virtuales
        
        Args:
            com1: Nombre del primer puerto
            com2: Nombre del segundo puerto
        
        Returns:
            bool: True si se eliminaron exitosamente
        """
        if not self.is_installed():
            return False
        
        try:
            # Primero necesitamos encontrar el número de par (n) para usar remove <n>
            # Listar puertos para encontrar el par
            result = subprocess.run([self.setupc_path, "list"], 
                                  capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
            
            # Buscar el par que contiene com1 y com2
            lines = result.stdout.split('\n')
            pair_number = None
            
            for line in lines:
                if com1 in line or com2 in line:
                    # Buscar CNCA<n> o CNCB<n> en la línea
                    if 'CNCA' in line:
                        # Extraer el número del par
                        parts = line.split()
                        for part in parts:
                            if part.startswith('CNCA'):
                                pair_number = part[4:]  # Extraer el número después de CNCA
                                break
                    elif 'CNCB' in line:
                        parts = line.split()
                        for part in parts:
                            if part.startswith('CNCB'):
                                pair_number = part[4:]  # Extraer el número después de CNCB
                                break
            
            if pair_number is not None:
                # Eliminar el par usando el número
                subprocess.run([self.setupc_path, "remove", pair_number], 
                             check=True, capture_output=True, timeout=10, cwd=self.com0com_path)
                logger.info(f"✅ Par de puertos {com1} y {com2} (par #{pair_number}) eliminado exitosamente")
                return True
            else:
                logger.warning(f"❌ No se pudo encontrar el par de puertos {com1} y {com2}")
                return False
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error al eliminar puertos: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return False
    
    def test_communication(self, com1: str, com2: str) -> bool:
        """
        Prueba la comunicación entre dos puertos COM
        
        Args:
            com1: Nombre del primer puerto
            com2: Nombre del segundo puerto
        
        Returns:
            bool: True si la comunicación funciona correctamente
        """
        try:
            # Abrir ambos puertos
            with serial.Serial(com1, 115200, timeout=1) as port1, \
                 serial.Serial(com2, 115200, timeout=1) as port2:
                
                # Enviar mensaje de prueba desde com1 a com2
                test_message = b"Hello from COM1!"
                port1.write(test_message)
                
                # Leer el mensaje en com2
                received = port2.read(len(test_message))
                
                if received == test_message:
                    logger.info(f"✅ Comunicación exitosa entre {com1} y {com2}")
                    return True
                else:
                    logger.error(f"❌ Error en comunicación: enviado={test_message}, recibido={received}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error al probar comunicación: {e}")
            return False 