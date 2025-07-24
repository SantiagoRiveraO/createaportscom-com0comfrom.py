import os
import subprocess
import time
import winreg
from typing import Tuple, Optional, List
import serial


class Com0comManager:
    """
    Clase para gestionar puertos COM virtuales usando com0com
    """
    
    def __init__(self):
        self.com0com_path = None
        self.setupc_path = None
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
            result = subprocess.run([self.setupc_path, "install", f"PortName={com1}", f"PortName={com2}"], 
                                   capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
            print(f"   Resultado: {result.stdout.strip()}")
            if result.returncode != 0:
                print(f"   Error: {result.stderr.strip()}")
                return False
            
            print(f"⚙️ Configurando parámetros de comunicación...")
            
            # Encontrar los identificadores CNCA y CNCB del par creado
            list_result = subprocess.run([self.setupc_path, "list"], 
                                       capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
            
            # Buscar el par que contiene com1 y com2
            lines = list_result.stdout.split('\n')
            cnca_id = None
            cncb_id = None
            
            for line in lines:
                if com1 in line and 'CNCA' in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith('CNCA'):
                            cnca_id = part
                            break
                elif com2 in line and 'CNCB' in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith('CNCB'):
                            cncb_id = part
                            break
            
            if cnca_id and cncb_id:
                # Configurar EmuBR=yes para ambos puertos (emulación de baudrate)
                result4 = subprocess.run([self.setupc_path, "change", cnca_id, "EmuBR=yes"], 
                                       capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
                print(f"   {cnca_id} EmuBR=yes: {result4.stdout.strip()}")
                
                result5 = subprocess.run([self.setupc_path, "change", cncb_id, "EmuBR=yes"], 
                                       capture_output=True, text=True, timeout=10, cwd=self.com0com_path)
                print(f"   {cncb_id} EmuBR=yes: {result5.stdout.strip()}")
            else:
                print(f"   ⚠️ No se pudieron encontrar los identificadores CNCA/CNCB para {com1} y {com2}")
            
            # Esperar un momento para que los cambios se apliquen
            time.sleep(2)
            
            print(f"✅ Puertos {com1} y {com2} creados y configurados exitosamente")
            return True
            
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout al crear puertos")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False
    
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