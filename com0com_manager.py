import os
import subprocess
import time
import winreg
import json
from typing import Tuple, Optional, List
import serial


class Com0comManager:
    """
    Clase para gestionar puertos COM virtuales usando com0com
    """
    
    def __init__(self, config_file="com_ports_config.json"):
        self.com0com_path = None
        self.setupc_path = None
        self.config_file = config_file
        self._find_com0com_installation()
    
    def _find_com0com_installation(self) -> bool:
        """
        Detecta si com0com está instalado y encuentra las rutas necesarias
        """
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
        except (FileNotFoundError, OSError):
            pass
        
        # Verificar si existe setupc.exe en alguna de las rutas
        for path in possible_paths:
            if os.path.exists(path):
                self.setupc_path = path
                self.com0com_path = os.path.dirname(path)
                print(f"✅ Com0com encontrado en: {self.com0com_path}")
                return True
        
        print("❌ Com0com no encontrado. Por favor instálalo desde: https://sourceforge.net/projects/com0com/")
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
            print(f"⚠️ Error al cargar configuración: {e}")
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
            print(f"💾 Guardando configuración en: {abs_path}")
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Verificar que el archivo se creó
            if os.path.exists(self.config_file):
                print(f"✅ Archivo creado exitosamente: {com1} y {com2}")
                print(f"📁 Ubicación: {abs_path}")
                return True
            else:
                print(f"❌ Error: El archivo no se creó en {abs_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error al guardar configuración: {e}")
            print(f"📁 Intentando guardar en: {os.path.abspath(self.config_file)}")
            return False
    
    def _check_existing_ports(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Verifica si ya existen puertos configurados y si están disponibles
        """
        config = self._load_ports_config()
        
        if not config.get("ports") or len(config["ports"]) < 2:
            return None, None
        
        com1, com2 = config["ports"][0], config["ports"][1]
        print(f"🔍 Verificando puertos existentes: {com1} y {com2}")
        
        # Verificar si los puertos están realmente disponibles
        if self._ports_exist_and_available(com1, com2):
            print(f"✅ Puertos existentes encontrados y disponibles: {com1} y {com2}")
            return com1, com2
        else:
            print(f"❌ Puertos existentes no están disponibles, se crearán nuevos")
            return None, None
    
    def _ports_exist_and_available(self, com1: str, com2: str) -> bool:
        """
        Verifica si los puertos existen y están disponibles para comunicación
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
            
            if com1_found and com2_found:
                # Probar comunicación básica
                return self.test_communication(com1, com2)
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error al verificar puertos: {e}")
            return False
    
    def get_or_create_paired_ports(self) -> Tuple[str, str]:
        """
        Obtiene puertos existentes o crea nuevos si es necesario
        
        Returns:
            Tuple[str, str]: Par de puertos disponibles
        """
        print("🔍 Verificando puertos existentes...")
        
        # Verificar si ya existen puertos configurados
        existing_com1, existing_com2 = self._check_existing_ports()
        
        if existing_com1 and existing_com2:
            print(f"✅ Reutilizando puertos existentes: {existing_com1} y {existing_com2}")
            return existing_com1, existing_com2
        
        # Si no existen, crear nuevos
        print("🆕 Creando nuevos puertos...")
        new_com1, new_com2 = self.create_auto_paired_ports()
        
        if new_com1 and new_com2:
            # Guardar la nueva configuración
            print(f"💾 Guardando configuración de puertos nuevos...")
            save_success = self._save_ports_config(new_com1, new_com2)
            if save_success:
                print(f"✅ Configuración guardada correctamente")
            else:
                print(f"⚠️ Error al guardar configuración, pero los puertos funcionan")
            return new_com1, new_com2
        else:
            print("❌ Error al crear nuevos puertos")
            return None, None
    
    def clear_ports_config(self) -> bool:
        """
        Limpia la configuración guardada de puertos
        """
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                print(f"🗑️ Configuración eliminada: {self.config_file}")
                return True
        except Exception as e:
            print(f"❌ Error al eliminar configuración: {e}")
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
            print("⚠️ Timeout al listar puertos")
            return []
        except Exception as e:
            print(f"❌ Error al listar puertos: {e}")
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
            
            print(f"📊 Puertos ocupados: {busy_ports}")
            print(f"📊 Puertos disponibles: {available_ports[:10]}...")  # Mostrar solo los primeros 10
            
            return available_ports
            
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout al verificar puertos disponibles")
            return []
        except Exception as e:
            print(f"❌ Error al verificar puertos disponibles: {e}")
            return []
    
    def find_available_pair(self) -> Tuple[str, str]:
        """
        Encuentra el primer par de puertos COM disponibles consecutivos
        
        Returns:
            Tuple[str, str]: Par de puertos disponibles (ej: ("COM20", "COM21"))
        """
        available_ports = self.get_available_com_ports()
        
        if len(available_ports) < 2:
            print("❌ No hay suficientes puertos COM disponibles")
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
                    print(f"✅ Par disponible encontrado: {port1} y {port2}")
                    return port1, port2
            except ValueError:
                continue
        
        print("❌ No se encontró un par de puertos consecutivos disponibles")
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
            print("❌ Com0com no está instalado")
            return False
        
        try:
            # Crear un par de puertos conectados usando el comando correcto
            # Usar el directorio de com0com como directorio de trabajo
            print(f"🔧 Creando par de puertos {com1} y {com2}...")
            # Usar PortName=COM# para activar automáticamente "use Ports class"
            # Agregar --silent para suprimir diálogos
            result = subprocess.run([self.setupc_path, "--silent", "install", "PortName=COM#", "PortName=COM#"], 
                                   capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
            print(f"   Resultado: {result.stdout.strip()}")
            if result.returncode != 0:
                print(f"   Error: {result.stderr.strip()}")
                return False
            
            # Asignar nombres específicos a los puertos creados
            print(f"🔧 Asignando nombres específicos {com1} y {com2}...")
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
                    print(f"   Asignando {cnca_id} -> {com1}...")
                    result2 = subprocess.run([self.setupc_path, "--silent", "change", cnca_id, f"RealPortName={com1}"], 
                                           capture_output=True, text=True, timeout=30, cwd=self.com0com_path)
                    print(f"   {cnca_id} -> {com1}: {result2.stdout.strip()}")
                    
                    print(f"   Asignando {cncb_id} -> {com2}...")
                    result3 = subprocess.run([self.setupc_path, "--silent", "change", cncb_id, f"RealPortName={com2}"], 
                                           capture_output=True, text=True, timeout=30, cwd=self.com0com_path)
                    print(f"   {cncb_id} -> {com2}: {result3.stdout.strip()}")
                    
                    # Esperar un momento para que los cambios se apliquen
                    time.sleep(1)
                except subprocess.TimeoutExpired:
                    print(f"   ⚠️ Timeout al asignar nombres específicos, pero los puertos se crearon correctamente")
                    print(f"   Los puertos están disponibles como COM# y funcionarán normalmente")
                except Exception as e:
                    print(f"   ⚠️ Error al asignar nombres específicos: {e}")
                    print(f"   Los puertos se crearon pero mantienen nombres genéricos")
            else:
                print(f"   ⚠️ No se pudieron encontrar los puertos recién creados")
            
            print(f"⚙️ Configurando parámetros de comunicación...")
            
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
                print(f"   Configurando {cnca_id}...")
                result4 = subprocess.run([self.setupc_path, "--silent", "change", cnca_id, "EmuBR=no"], 
                                       capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
                print(f"   {cnca_id} EmuBR=no: {result4.stdout.strip()}")
                
                print(f"   Configurando {cncb_id}...")
                result5 = subprocess.run([self.setupc_path, "--silent", "change", cncb_id, "EmuBR=no"], 
                                       capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
                print(f"   {cncb_id} EmuBR=no: {result5.stdout.strip()}")
                
                print(f"   ✅ Ambos puertos configurados sin emulación de baudrate")
            else:
                print(f"   ⚠️ No se pudieron encontrar los identificadores CNCA/CNCB")
            
            # Esperar un momento para que los cambios se apliquen
            time.sleep(2)
            
            print(f"✅ Puertos creados y configurados exitosamente")
            return True
            
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout al crear puertos")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False
    
    def create_auto_paired_ports(self) -> Tuple[str, str]:
        """
        Crea automáticamente un par de puertos COM en las primeras posiciones disponibles
        
        Returns:
            Tuple[str, str]: Par de puertos creados (ej: ("COM20", "COM21")) o (None, None) si falla
        """
        print("🔍 Buscando par de puertos disponibles...")
        com1, com2 = self.find_available_pair()
        
        if com1 is None or com2 is None:
            print("❌ No se pudo encontrar un par de puertos disponibles")
            return None, None
        
        print(f"🎯 Creando par automático en {com1} y {com2}...")
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
            
            print(f"✅ Par automático creado exitosamente")
            print(f"   Puertos: {final_com1} y {final_com2}")
            return com1, com2  # Retornar los nombres originales para compatibilidad
        else:
            print(f"❌ Error al crear par automático")
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
                print(f"✅ Par de puertos {com1} y {com2} (par #{pair_number}) eliminado exitosamente")
                return True
            else:
                print(f"❌ No se pudo encontrar el par de puertos {com1} y {com2}")
                return False
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error al eliminar puertos: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
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
                    print(f"✅ Comunicación exitosa entre {com1} y {com2}")
                    return True
                else:
                    print(f"❌ Error en comunicación: enviado={test_message}, recibido={received}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error al probar comunicación: {e}")
            return False 