#!/usr/bin/env python3
"""
Aplicación principal de escritorio
Integra setup inicial y funcionalidad de escucha de puertos COM
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import serial
import threading
from datetime import datetime
import os
import sys
import ctypes

# Agregar el directorio src al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from setup_manager import SetupManager
from com0com_manager import Com0comManager

def verify_admin_privileges():
    """
    Verifica que la aplicación tenga permisos de administrador
    Esta función se ejecuta antes de cualquier operación
    """
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            # Crear ventana temporal para mostrar error
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
            sys.exit(1)
        
        print("✅ Permisos de administrador verificados correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar permisos de administrador: {e}")
        # Crear ventana temporal para mostrar error
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"Error al verificar permisos de administrador: {e}")
        root.destroy()
        sys.exit(1)

class MainApplication:
    def __init__(self):
        # Verificar permisos de administrador ANTES de crear la ventana
        verify_admin_privileges()
        
        self.root = tk.Tk()
        self.setup_app_window()
        
        # Variables
        self.serial_port_input = None   # Puerto de entrada (donde recibimos JSONs)
        self.serial_port_output = None  # Puerto de salida (donde enviamos JSONs)
        self.is_listening_input = False
        self.is_listening_output = False
        self.config_file = "config/com_ports_config.json"
        self.message_count = 0
        
        # Managers
        self.setup_manager = SetupManager()
        self.com_manager = Com0comManager(self.config_file)
        
        # Ejecutar setup inicial
        self.run_initial_setup()
        
    def setup_app_window(self):
        """Configurar la ventana principal de la aplicación"""
        self.root.title("CHINO - Monitor de Puertos COM")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Configurar menú
        self.create_menu()
        
        # Configurar grid principal
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
    def create_menu(self):
        """Crear menú de la aplicación"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Reconfigurar Puertos", command=self.reconfigure_ports)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.on_closing)
        
        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Ver Configuración", command=self.show_config)
        tools_menu.add_command(label="Limpiar Logs", command=self.clear_text)
        tools_menu.add_separator()
        tools_menu.add_command(label="Reconectar", command=self.reconnect)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        
    def run_initial_setup(self):
        """Ejecutar configuración inicial"""
        print("🚀 Iniciando aplicación...")
        
        # Mostrar splash screen
        self.show_splash_screen()
        
        # Ejecutar setup en thread separado
        def setup_thread():
            success = self.setup_manager.run_initial_setup()
            
            # Cerrar splash y mostrar interfaz principal
            self.root.after(0, lambda: self.finish_setup(success))
        
        thread = threading.Thread(target=setup_thread, daemon=True)
        thread.start()
        
    def show_splash_screen(self):
        """Mostrar pantalla de carga inicial"""
        self.splash = tk.Toplevel(self.root)
        self.splash.title("Iniciando...")
        self.splash.geometry("400x200")
        self.splash.resizable(False, False)
        self.splash.transient(self.root)
        self.splash.grab_set()
        
        # Centrar ventana
        self.splash.update_idletasks()
        x = (self.splash.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.splash.winfo_screenheight() // 2) - (200 // 2)
        self.splash.geometry(f"400x200+{x}+{y}")
        
        # Frame principal
        main_frame = ttk.Frame(self.splash, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="CHINO", 
                               font=("Arial", 24, "bold"))
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="Monitor de Puertos COM", 
                                  font=("Arial", 12))
        subtitle_label.pack(pady=(0, 20))
        
        # Mensaje de estado
        self.status_var = tk.StringVar(value="Iniciando aplicación...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=(0, 10))
        
        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X)
        self.progress.start()
        
    def finish_setup(self, success):
        """Finalizar setup y mostrar interfaz principal"""
        # Cerrar splash
        if hasattr(self, 'splash'):
            self.splash.destroy()
        
        if success:
            # Crear interfaz principal
            self.create_main_interface()
            print("✅ Aplicación iniciada correctamente")
        else:
            # Mostrar error y cerrar
            messagebox.showerror("Error de Inicio", 
                               "No se pudo completar la configuración inicial.\n"
                               "La aplicación se cerrará.")
            self.root.destroy()
    
    def create_main_interface(self):
        """Crear la interfaz principal de la aplicación"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="🔍 CHINO - Monitor de Puertos COM", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 10))
        
        # Frame de configuración de puertos
        config_frame = ttk.LabelFrame(main_frame, text="Configuración de Puertos", padding="5")
        config_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(3, weight=1)
        
        # Puerto COM Entrada
        ttk.Label(config_frame, text="Puerto Entrada:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.port_input_var = tk.StringVar()
        self.port_input_combo = ttk.Combobox(config_frame, textvariable=self.port_input_var, state="readonly", width=10)
        self.port_input_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Estado de conexión entrada
        self.status_input_var = tk.StringVar(value="⏳ Conectando...")
        status_input_label = ttk.Label(config_frame, textvariable=self.status_input_var, 
                                      foreground="orange", font=("Arial", 10, "bold"))
        status_input_label.grid(row=0, column=2, padx=(0, 20))
        
        # Puerto COM Salida
        ttk.Label(config_frame, text="Puerto Salida:").grid(row=0, column=3, sticky=tk.W, padx=(0, 5))
        self.port_output_var = tk.StringVar()
        self.port_output_combo = ttk.Combobox(config_frame, textvariable=self.port_output_var, state="readonly", width=10)
        self.port_output_combo.grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        
        # Botón conectar puerto de salida
        self.connect_output_btn = ttk.Button(config_frame, text="🔌 Conectar Salida", command=self.connect_output_port)
        self.connect_output_btn.grid(row=0, column=5, padx=(0, 10))
        
        # Estado de conexión salida
        self.status_output_var = tk.StringVar(value="❌ Desconectado")
        status_output_label = ttk.Label(config_frame, textvariable=self.status_output_var, 
                                       foreground="red", font=("Arial", 10, "bold"))
        status_output_label.grid(row=0, column=6)
        
        # Cargar puertos disponibles y conectar automáticamente
        self.load_ports_config()
        
        # Área de texto para mostrar JSONs
        text_frame = ttk.LabelFrame(main_frame, text="Mensajes y Respuestas", padding="5")
        text_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        # Texto con scroll
        self.text_area = scrolledtext.ScrolledText(text_frame, height=20, width=80, 
                                                   font=("Consolas", 10))
        self.text_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame de controles
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=4, pady=(10, 0))
        
        # Botón limpiar
        clear_btn = ttk.Button(control_frame, text="🗑️ Limpiar", command=self.clear_text)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Contador de mensajes
        self.counter_var = tk.StringVar(value="Mensajes: 0")
        counter_label = ttk.Label(control_frame, textvariable=self.counter_var)
        counter_label.pack(side=tk.LEFT)
        
        # Mostrar mensaje de bienvenida
        self.log_message("🚀 CHINO iniciado correctamente")
        self.log_message("📁 Configuración cargada desde archivo")
        self.log_message("📡 Puerto de entrada conectado automáticamente")
        self.log_message("📋 Selecciona puerto de salida y haz clic en '🔌 Conectar Salida'")
        
    def load_ports_config(self):
        """Cargar configuración de puertos desde JSON y mostrar todos los puertos COM del sistema"""
        try:
            # Obtener todos los puertos COM del sistema
            all_ports = self.get_all_com_ports()
            
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                created_ports = config.get('ports', [])
                if len(created_ports) >= 2:
                    # Agregar todos los puertos al combo
                    self.port_input_combo['values'] = all_ports
                    self.port_output_combo['values'] = all_ports
                    
                    # Seleccionar automáticamente el puerto de mayor número de los creados
                    # (el listener se conecta al puerto mayor, el sistema externo al menor)
                    port1, port2 = created_ports[0], created_ports[1]
                    
                    # Extraer números de puerto (ej: "COM10" -> 10)
                    try:
                        num1 = int(port1[3:])  # Extraer número después de "COM"
                        num2 = int(port2[3:])  # Extraer número después de "COM"
                        
                        # Seleccionar el puerto de mayor número de los creados
                        if num2 > num1:
                            default_input_port = port2  # Puerto mayor
                            default_output_port = port1  # Puerto menor
                            self.log_message(f"📡 Puerto de entrada por defecto: {port2} (mayor de los creados)")
                            self.log_message(f"📡 Puerto de salida por defecto: {port1} (menor de los creados)")
                        else:
                            default_input_port = port1  # Puerto mayor
                            default_output_port = port2  # Puerto menor
                            self.log_message(f"📡 Puerto de entrada por defecto: {port1} (mayor de los creados)")
                            self.log_message(f"📡 Puerto de salida por defecto: {port2} (menor de los creados)")
                        
                        self.port_input_combo.set(default_input_port)
                        self.port_output_combo.set(default_output_port)
                        
                        # CONECTAR automáticamente SOLO el puerto de entrada
                        self.connect_input_port_only(default_input_port)
                        
                    except ValueError:
                        # Si no se pueden extraer números, usar el segundo puerto por defecto
                        self.port_input_combo.set(port2)
                        self.port_output_combo.set(port1)
                        self.log_message(f"📡 Puerto de entrada por defecto: {port2}")
                        self.log_message(f"📡 Puerto de salida por defecto: {port1}")
                        # CONECTAR automáticamente SOLO el puerto de entrada
                        self.connect_input_port_only(port2)
                    
                    self.log_message(f"📁 Puertos creados: {port1} y {port2}")
                    self.log_message(f"📋 Puertos disponibles en el sistema: {len(all_ports)} puertos")
                    
                    # Configurar eventos para cambiar puerto INDEPENDIENTEMENTE
                    self.port_input_combo.bind('<<ComboboxSelected>>', self.on_input_port_changed)
                    self.port_output_combo.bind('<<ComboboxSelected>>', self.on_output_port_changed)
                    
                else:
                    self.log_message("⚠️ No hay puertos configurados en el JSON")
                    if all_ports:
                        # Si no hay configuración, usar el primer puerto disponible
                        self.port_input_combo['values'] = all_ports
                        self.port_output_combo['values'] = all_ports
                        self.port_input_combo.set(all_ports[0])
                        self.port_output_combo.set(all_ports[0])
                        self.log_message(f"📋 Usando primer puerto disponible: {all_ports[0]}")
                        # CONECTAR automáticamente SOLO el puerto de entrada
                        self.connect_input_port_only(all_ports[0])
                        self.port_input_combo.bind('<<ComboboxSelected>>', self.on_input_port_changed)
                        self.port_output_combo.bind('<<ComboboxSelected>>', self.on_output_port_changed)
            else:
                self.log_message("❌ Archivo de configuración no encontrado")
                if all_ports:
                    # Si no hay configuración, usar el primer puerto disponible
                    self.port_input_combo['values'] = all_ports
                    self.port_output_combo['values'] = all_ports
                    self.port_input_combo.set(all_ports[0])
                    self.port_output_combo.set(all_ports[0])
                    self.log_message(f"📋 Usando primer puerto disponible: {all_ports[0]}")
                    # CONECTAR automáticamente SOLO el puerto de entrada
                    self.connect_input_port_only(all_ports[0])
                    self.port_input_combo.bind('<<ComboboxSelected>>', self.on_input_port_changed)
                    self.port_output_combo.bind('<<ComboboxSelected>>', self.on_output_port_changed)
        except Exception as e:
            self.log_message(f"❌ Error al cargar configuración: {e}")
    
    def configure_serial_port(self, port_name):
        """Configurar puerto serial optimizado para máxima velocidad"""
        port = serial.Serial(
            port=port_name,
            baudrate=115200,
            timeout=0.01,  # Timeout mínimo para máxima velocidad
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            write_timeout=0.01,  # Timeout mínimo para escritura
            inter_byte_timeout=None  # Sin timeout entre bytes
        )
        
        # Configurar buffers específicos para Windows
        if hasattr(port, 'set_buffer_size'):
            try:
                port.set_buffer_size(rx_size=65536, tx_size=65536)
            except:
                pass  # Si no se puede configurar, continuar
        
        # Configurar parámetros específicos de Windows
        if hasattr(port, 'set_low_latency_mode'):
            try:
                port.set_low_latency_mode(True)
            except:
                pass  # Si no se puede configurar, continuar
        
        # Configurar parámetros adicionales de Windows para estabilidad
        try:
            import win32file
            import win32api
            
            # Obtener handle del puerto
            handle = win32file.CreateFile(
                f"\\\\.\\{port_name}",
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                win32file.FILE_ATTRIBUTE_NORMAL,
                None
            )
            
            # Configurar timeouts de Windows para máxima velocidad
            timeouts = win32file.COMMTIMEOUTS()
            timeouts.ReadIntervalTimeout = 0xFFFFFFFF  # No timeout entre bytes
            timeouts.ReadTotalTimeoutConstant = 10     # 10ms timeout total (mínimo)
            timeouts.ReadTotalTimeoutMultiplier = 0    # No multiplicador
            timeouts.WriteTotalTimeoutConstant = 10    # 10ms timeout escritura (mínimo)
            timeouts.WriteTotalTimeoutMultiplier = 0   # No multiplicador
            
            win32file.SetCommTimeouts(handle, timeouts)
            
            # Configurar parámetros del puerto
            dcb = win32file.GetCommState(handle)
            dcb.BaudRate = 115200
            dcb.ByteSize = 8
            dcb.Parity = 0  # No parity
            dcb.StopBits = 0  # 1 stop bit
            win32file.SetCommState(handle, dcb)
            
            win32file.CloseHandle(handle)
            
        except Exception as e:
            # Si falla la configuración de Windows, continuar con configuración básica
            pass
        
        return port
    
    def connect_input_port_only(self, input_port):
        """Conectar SOLO el puerto de entrada automáticamente"""
        if not input_port:
            self.log_message("❌ No hay puerto de entrada disponible para conectar")
            self.status_input_var.set("❌ Error")
            return
        
        try:
            # Configurar puerto serial de entrada optimizado
            self.serial_port_input = self.configure_serial_port(input_port)
            
            self.is_listening_input = True
            self.status_input_var.set("✅ Conectado")
            
            # Iniciar thread de escucha de entrada
            self.listen_input_thread = threading.Thread(target=self.listen_for_input_data, daemon=True)
            self.listen_input_thread.start()
            
            self.log_message(f"🔌 Conectado automáticamente a {input_port} (entrada)")
            self.log_message("📡 Esperando datos JSON de entrada...")
            self.log_message("📋 Selecciona puerto de salida y haz clic en '🔌 Conectar Salida'")
            
        except Exception as e:
            self.log_message(f"❌ Error al conectar puerto de entrada: {e}")
            self.status_input_var.set("❌ Error de conexión")
            # Intentar reconexión automática
            self.auto_reconnect_ports()
    
    def on_input_port_changed(self, event):
        """Manejar cambio de puerto de entrada"""
        input_port = self.port_input_var.get()
        self.log_message(f"📡 Puerto de entrada cambiado a: {input_port}")
        
        # Reconectar automáticamente el puerto de entrada
        if self.is_listening_input:
            self.is_listening_input = False
            if self.serial_port_input and self.serial_port_input.is_open:
                self.serial_port_input.close()
            self.log_message("🔌 Desconectado del puerto de entrada anterior")
        
        self.connect_input_port_only(input_port)
    
    def on_output_port_changed(self, event):
        """Manejar cambio de puerto de salida"""
        output_port = self.port_output_var.get()
        self.log_message(f"📡 Puerto de salida cambiado a: {output_port}")
        # NO conectar automáticamente - el usuario debe usar el botón
    
    def connect_output_port(self):
        """Conectar el puerto de salida seleccionado"""
        output_port = self.port_output_var.get()
        
        if not output_port:
            self.log_message("❌ No hay puerto de salida seleccionado")
            return
        
        if self.is_listening_output:
            self.log_message("✅ Puerto de salida ya está conectado")
            return
        
        try:
            # Configurar puerto serial de salida optimizado
            self.serial_port_output = self.configure_serial_port(output_port)
            
            self.is_listening_output = True
            self.status_output_var.set("✅ Conectado")
            
            # Iniciar thread de escucha de respuestas de salida
            self.listen_output_thread = threading.Thread(target=self.listen_for_output_responses, daemon=True)
            self.listen_output_thread.start()
            
            self.log_message(f"🔌 Puerto de salida conectado a {output_port}")
            self.log_message("📡 Sistema completo: Esperando datos JSON...")
            
        except Exception as e:
            self.log_message(f"❌ Error al conectar puerto de salida: {e}")
            self.status_output_var.set("❌ Error de conexión")
            # Intentar reconexión automática
            self.auto_reconnect_ports()
    
    def get_all_com_ports(self):
        """Obtener todos los puertos COM disponibles en el sistema"""
        import serial.tools.list_ports
        
        try:
            # Obtener todos los puertos COM
            ports = [port.device for port in serial.tools.list_ports.comports()]
            ports.sort(key=lambda x: int(x[3:]) if x[3:].isdigit() else 0)  # Ordenar por número
            return ports
        except Exception as e:
            self.log_message(f"⚠️ Error al obtener puertos del sistema: {e}")
            return []
    
    def listen_for_input_data(self):
        """Escuchar datos del puerto de entrada y reenviarlos al puerto de salida"""
        import time
        
        error_count = 0
        consecutive_empty_reads = 0
        
        while self.is_listening_input:
            try:
                # Verificar que el puerto esté disponible y abierto
                if not self.serial_port_input or not self.serial_port_input.is_open:
                    time.sleep(0.5)  # Pausa más larga si el puerto no está disponible
                    continue
                
                # Leer datos disponibles - OPTIMIZADO PARA VELOCIDAD
                if self.serial_port_input.in_waiting > 0:
                    data = self.serial_port_input.read(self.serial_port_input.in_waiting)
                    if data:
                        json_str = data.decode('utf-8', errors='ignore').strip()
                        # Reenviar al puerto de salida (JSONs son perfectos)
                        self.forward_to_output(json_str)
                        error_count = 0  # Resetear contador de errores si hay datos
                        consecutive_empty_reads = 0  # Resetear contador de lecturas vacías
                else:
                    consecutive_empty_reads += 1
                    # Pausa mínima para máxima velocidad
                    if consecutive_empty_reads < 50:
                        time.sleep(0.001)  # 1ms para máxima velocidad
                    elif consecutive_empty_reads < 200:
                        time.sleep(0.005)  # 5ms para velocidad moderada
                    else:
                        time.sleep(0.01)   # 10ms para evitar saturación
                
            except PermissionError as e:
                error_count += 1
                if error_count >= 10:  # Aumentar a 10 errores antes de reconexión
                    self.log_message("🔄 Intentando reconexión automática por errores de permisos...")
                    self.auto_reconnect_ports()
                    # NO hacer break, continuar escuchando
                    error_count = 0  # Resetear contador después de reconexión
                elif error_count <= 3:  # Solo mostrar los primeros 3 errores
                    self.log_message(f"🔒 Puerto de entrada bloqueado: {e}")
                time.sleep(2.0)  # Pausa más larga para errores de permisos
                continue
            except Exception as e:
                error_count += 1
                if error_count >= 10:  # Aumentar a 10 errores antes de reconexión
                    self.log_message("🔄 Intentando reconexión automática por errores...")
                    self.auto_reconnect_ports()
                    # NO hacer break, continuar escuchando
                    error_count = 0  # Resetear contador después de reconexión
                elif error_count <= 3:  # Solo mostrar los primeros 3 errores
                    self.log_message(f"⚠️ Error en escucha de entrada: {e}")
                time.sleep(1.0)  # Pausa más larga para otros errores
                continue
        
        # Solo mostrar este mensaje si realmente se está cerrando la aplicación
        if not self.is_listening_input:
            self.log_message("🔌 Thread de escucha de entrada terminado (aplicación cerrada)")
        else:
            self.log_message("⚠️ Thread de escucha de entrada terminado inesperadamente")
            # Intentar reiniciar el hilo automáticamente
            self.restart_input_thread()
    
    def listen_for_output_responses(self):
        """Escuchar respuestas del puerto de salida y reenviarlas al puerto de entrada"""
        import time
        
        error_count = 0
        consecutive_empty_reads = 0
        
        while self.is_listening_output:
            try:
                # Verificar que el puerto esté disponible y abierto
                if not self.serial_port_output or not self.serial_port_output.is_open:
                    time.sleep(0.5)  # Pausa más larga si el puerto no está disponible
                    continue
                
                # Leer datos disponibles - OPTIMIZADO PARA VELOCIDAD
                if self.serial_port_output.in_waiting > 0:
                    data = self.serial_port_output.read(self.serial_port_output.in_waiting)
                    if data:
                        json_str = data.decode('utf-8', errors='ignore').strip()
                        # Reenviar al puerto de entrada (JSONs son perfectos)
                        self.forward_to_input(json_str)
                        error_count = 0  # Resetear contador de errores si hay datos
                        consecutive_empty_reads = 0  # Resetear contador de lecturas vacías
                else:
                    consecutive_empty_reads += 1
                    # Pausa mínima para máxima velocidad
                    if consecutive_empty_reads < 50:
                        time.sleep(0.001)  # 1ms para máxima velocidad
                    elif consecutive_empty_reads < 200:
                        time.sleep(0.005)  # 5ms para velocidad moderada
                    else:
                        time.sleep(0.01)   # 10ms para evitar saturación
                
            except PermissionError as e:
                error_count += 1
                if error_count >= 10:  # Aumentar a 10 errores antes de reconexión
                    self.log_message("🔄 Intentando reconexión automática por errores de permisos...")
                    self.auto_reconnect_ports()
                    # NO hacer break, continuar escuchando
                    error_count = 0  # Resetear contador después de reconexión
                elif error_count <= 3:  # Solo mostrar los primeros 3 errores
                    self.log_message(f"🔒 Puerto de salida bloqueado: {e}")
                time.sleep(2.0)  # Pausa más larga para errores de permisos
                continue
            except Exception as e:
                error_count += 1
                if error_count >= 10:  # Aumentar a 10 errores antes de reconexión
                    self.log_message("🔄 Intentando reconexión automática por errores...")
                    self.auto_reconnect_ports()
                    # NO hacer break, continuar escuchando
                    error_count = 0  # Resetear contador después de reconexión
                elif error_count <= 3:  # Solo mostrar los primeros 3 errores
                    self.log_message(f"⚠️ Error en escucha de salida: {e}")
                time.sleep(1.0)  # Pausa más larga para otros errores
                continue
        
        # Solo mostrar este mensaje si realmente se está cerrando la aplicación
        if not self.is_listening_output:
            self.log_message("🔌 Thread de escucha de salida terminado (aplicación cerrada)")
        else:
            self.log_message("⚠️ Thread de escucha de salida terminado inesperadamente")
            # Intentar reiniciar el hilo automáticamente
            self.restart_output_thread()
    
    def forward_to_output(self, json_str):
        """Reenviar JSON recibido al puerto de salida - OPTIMIZADO PARA VELOCIDAD"""
        try:
            if self.serial_port_output and self.serial_port_output.is_open:
                # Enviar JSON tal cual - SIN FLUSH para máxima velocidad
                self.serial_port_output.write(json_str.encode('utf-8'))
                # NO usar flush() - deja que el buffer se envíe automáticamente
                
                # Mostrar en interfaz (asíncrono para no bloquear)
                self.message_count += 1
                self.root.after_idle(self.display_sent_message, json_str)
                
        except Exception as e:
            self.log_message(f"❌ Error al reenviar a salida: {e}")
    
    def forward_to_input(self, json_str):
        """Reenviar respuesta recibida al puerto de entrada - OPTIMIZADO PARA VELOCIDAD"""
        try:
            if self.serial_port_input and self.serial_port_input.is_open:
                # Enviar respuesta tal cual - SIN FLUSH para máxima velocidad
                self.serial_port_input.write(json_str.encode('utf-8'))
                # NO usar flush() - deja que el buffer se envíe automáticamente
                
                # Mostrar en interfaz (asíncrono para no bloquear)
                self.root.after_idle(self.display_received_response, json_str)
                
        except Exception as e:
            self.log_message(f"❌ Error al reenviar respuesta a entrada: {e}")
    
    def display_sent_message(self, json_str):
        """Mostrar mensaje enviado en la interfaz"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Formatear JSON para mostrar
        try:
            json_data = json.loads(json_str)
            formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
        except:
            formatted_json = json_str
        
        # Agregar al área de texto
        self.text_area.insert(tk.END, f"\n{'='*60}\n")
        self.text_area.insert(tk.END, f"📤 Mensaje #{self.message_count} - {timestamp}\n")
        self.text_area.insert(tk.END, f"Enviado a {self.port_output_var.get()}: {formatted_json}\n")
        self.text_area.insert(tk.END, f"{'='*60}\n")
        
        # Scroll al final
        self.text_area.see(tk.END)
        
        # Actualizar contador
        self.counter_var.set(f"Mensajes: {self.message_count}")
    
    def display_received_response(self, json_str):
        """Mostrar respuesta recibida en la interfaz"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Formatear JSON para mostrar
        try:
            json_data = json.loads(json_str)
            formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
        except:
            formatted_json = json_str
        
        # Agregar al área de texto
        self.text_area.insert(tk.END, f"\n{'='*60}\n")
        self.text_area.insert(tk.END, f"📥 Respuesta - {timestamp}\n")
        self.text_area.insert(tk.END, f"Recibida de {self.port_output_var.get()}: {formatted_json}\n")
        self.text_area.insert(tk.END, f"Reenviada a {self.port_input_var.get()}\n")
        self.text_area.insert(tk.END, f"{'='*60}\n")
        
        # Scroll al final
        self.text_area.see(tk.END)
    
    def log_message(self, message):
        """Agregar mensaje de log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Usar after para thread safety
        self.root.after(0, lambda: self.text_area.insert(tk.END, log_message))
        self.root.after(0, lambda: self.text_area.see(tk.END))
    
    def clear_text(self):
        """Limpiar área de texto"""
        self.text_area.delete(1.0, tk.END)
        self.message_count = 0
        self.counter_var.set("Mensajes: 0")
    
    def reconfigure_ports(self):
        """Reconfigurar puertos COM"""
        if messagebox.askyesno("Reconfigurar", 
                              "¿Deseas reconfigurar los puertos COM?\n\n"
                              "Esto eliminará la configuración actual y creará nuevos puertos."):
            # Limpiar configuración existente
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            
            # Ejecutar setup nuevamente
            success = self.setup_manager.run_initial_setup()
            
            if success:
                # Recargar configuración
                self.load_ports_config()
                messagebox.showinfo("Reconfiguración", "Puertos reconfigurados correctamente")
            else:
                messagebox.showerror("Error", "No se pudo reconfigurar los puertos")
    
    def show_config(self):
        """Mostrar configuración actual"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                config_text = json.dumps(config, indent=2, ensure_ascii=False)
                
                # Crear ventana de configuración
                config_window = tk.Toplevel(self.root)
                config_window.title("Configuración Actual")
                config_window.geometry("500x400")
                
                # Área de texto
                text_area = scrolledtext.ScrolledText(config_window, font=("Consolas", 10))
                text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_area.insert(tk.END, config_text)
                text_area.config(state=tk.DISABLED)
                
            else:
                messagebox.showinfo("Configuración", "No hay archivo de configuración")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer configuración: {e}")
    
    def show_about(self):
        """Mostrar información sobre la aplicación"""
        about_text = """CHINO - Monitor de Puertos COM

Versión: 1.0
Desarrollado para monitorear puertos COM virtuales
y recibir datos JSON en tiempo real.

Características:
• Configuración automática de puertos COM
• Escucha en tiempo real de datos JSON
• Interfaz gráfica intuitiva
• Persistencia de configuración

© 2025 - Todos los derechos reservados"""
        
        messagebox.showinfo("Acerca de", about_text)
    
    def auto_reconnect_ports(self):
        """Reconexión automática cuando hay errores de conexión"""
        import time
        
        input_port = self.port_input_var.get()
        output_port = self.port_output_var.get()
        
        if not input_port or not output_port:
            self.log_message("❌ No hay puertos configurados para reconexión automática")
            return
        
        self.log_message("🔄 Iniciando reconexión automática...")
        
        # Desconectar ambos puertos de forma segura
        if self.is_listening_input:
            self.is_listening_input = False
            if self.serial_port_input and self.serial_port_input.is_open:
                try:
                    self.serial_port_input.close()
                except:
                    pass  # Ignorar errores al cerrar
        
        if self.is_listening_output:
            self.is_listening_output = False
            if self.serial_port_output and self.serial_port_output.is_open:
                try:
                    self.serial_port_output.close()
                except:
                    pass  # Ignorar errores al cerrar
        
        # Esperar más tiempo para que se liberen completamente los puertos
        time.sleep(3.0)
        
        # Actualizar estados
        self.status_input_var.set("⏳ Reconectando...")
        self.status_output_var.set("⏳ Reconectando...")
        
        # Intentar reconectar con reintentos
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Reconectar puerto de entrada
                self.connect_input_port_only(input_port)
                
                # Si el puerto de salida estaba conectado, reconectarlo también
                if self.port_output_var.get():
                    self.connect_output_port()
                
                self.log_message(f"✅ Reconexión automática completada (intento {attempt + 1})")
                return  # Salir si fue exitoso
                
            except Exception as e:
                self.log_message(f"❌ Error en reconexión automática (intento {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2.0)  # Esperar antes del siguiente intento
                else:
                    self.status_input_var.set("❌ Error")
                    self.status_output_var.set("❌ Error")
                    self.log_message("❌ Reconexión automática falló después de 3 intentos")
    
    def restart_input_thread(self):
        """Reiniciar el hilo de escucha de entrada si se cierra inesperadamente"""
        import time
        
        if not self.is_listening_input:
            return  # No reiniciar si ya se está cerrando intencionalmente
        
        self.log_message("🔄 Reiniciando hilo de escucha de entrada...")
        
        # Esperar un momento antes de reiniciar
        time.sleep(1.0)
        
        try:
            # Verificar que el puerto esté conectado
            if self.serial_port_input and self.serial_port_input.is_open:
                # Reiniciar el hilo
                self.listen_input_thread = threading.Thread(target=self.listen_for_input_data, daemon=True)
                self.listen_input_thread.start()
                self.log_message("✅ Hilo de escucha de entrada reiniciado")
            else:
                self.log_message("❌ No se puede reiniciar hilo: puerto no conectado")
        except Exception as e:
            self.log_message(f"❌ Error al reiniciar hilo de entrada: {e}")
    
    def restart_output_thread(self):
        """Reiniciar el hilo de escucha de salida si se cierra inesperadamente"""
        import time
        
        if not self.is_listening_output:
            return  # No reiniciar si ya se está cerrando intencionalmente
        
        self.log_message("🔄 Reiniciando hilo de escucha de salida...")
        
        # Esperar un momento antes de reiniciar
        time.sleep(1.0)
        
        try:
            # Verificar que el puerto esté conectado
            if self.serial_port_output and self.serial_port_output.is_open:
                # Reiniciar el hilo
                self.listen_output_thread = threading.Thread(target=self.listen_for_output_responses, daemon=True)
                self.listen_output_thread.start()
                self.log_message("✅ Hilo de escucha de salida reiniciado")
            else:
                self.log_message("❌ No se puede reiniciar hilo: puerto no conectado")
        except Exception as e:
            self.log_message(f"❌ Error al reiniciar hilo de salida: {e}")
    
    def force_flush_ports(self):
        """Forzar el envío inmediato de datos en buffers (para máxima velocidad)"""
        try:
            if self.serial_port_input and self.serial_port_input.is_open:
                self.serial_port_input.flush()
            if self.serial_port_output and self.serial_port_output.is_open:
                self.serial_port_output.flush()
        except Exception as e:
            pass  # Ignorar errores de flush
    
    def reconnect(self):
        """Reconectar a los puertos COM actuales"""
        input_port = self.port_input_var.get()
        output_port = self.port_output_var.get()
        
        if input_port and output_port:
            self.log_message(f"🔄 Reconectando: {input_port} → {output_port}")
            
            # Desconectar primero
            if self.is_listening_input:
                self.is_listening_input = False
                if self.serial_port_input and self.serial_port_input.is_open:
                    self.serial_port_input.close()
            
            if self.is_listening_output:
                self.is_listening_output = False
                if self.serial_port_output and self.serial_port_output.is_open:
                    self.serial_port_output.close()
            
            # Reconectar ambos puertos
            self.status_input_var.set("⏳ Reconectando...")
            self.status_output_var.set("⏳ Reconectando...")
            self.connect_to_port_auto(input_port, output_port)
        else:
            self.log_message("❌ No hay puertos seleccionados para reconectar")
    
    def connect_to_port_auto(self, input_port, output_port):
        """Conectar automáticamente a los puertos COM de entrada y salida"""
        if not input_port or not output_port:
            self.log_message("❌ No hay puertos disponibles para conectar")
            self.status_input_var.set("❌ Error")
            self.status_output_var.set("❌ Error")
            return
        
        try:
            # Configurar puertos seriales optimizados
            self.serial_port_input = self.configure_serial_port(input_port)
            self.serial_port_output = self.configure_serial_port(output_port)
            
            self.is_listening_input = True
            self.is_listening_output = True
            self.status_input_var.set("✅ Conectado")
            self.status_output_var.set("✅ Conectado")
            
            # Iniciar thread de escucha de entrada
            self.listen_input_thread = threading.Thread(target=self.listen_for_input_data, daemon=True)
            self.listen_input_thread.start()
            
            # Iniciar thread de escucha de respuestas de salida
            self.listen_output_thread = threading.Thread(target=self.listen_for_output_responses, daemon=True)
            self.listen_output_thread.start()
            
            self.log_message(f"🔌 Conectado automáticamente a {input_port} (entrada) y {output_port} (salida)")
            self.log_message("📡 Esperando datos JSON...")
            
        except Exception as e:
            self.log_message(f"❌ Error al conectar automáticamente: {e}")
            self.status_input_var.set("❌ Error de conexión")
            self.status_output_var.set("❌ Error de conexión")
            # Intentar reconexión automática
            self.auto_reconnect_ports()
    
    def on_closing(self):
        """Manejar cierre de ventana"""
        if self.is_listening_input:
            self.is_listening_input = False
            if self.serial_port_input and self.serial_port_input.is_open:
                self.serial_port_input.close()
            self.log_message("🔌 Desconectado del puerto de entrada al cerrar aplicación")
        
        if self.is_listening_output:
            self.is_listening_output = False
            if self.serial_port_output and self.serial_port_output.is_open:
                self.serial_port_output.close()
            self.log_message("🔌 Desconectado del puerto de salida al cerrar aplicación")
        
        if messagebox.askokcancel("Salir", "¿Deseas salir de la aplicación?"):
            self.root.destroy()
    
    def run(self):
        """Ejecutar la aplicación"""
        # Configurar cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Centrar ventana
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Ejecutar aplicación
        self.root.mainloop()

def main():
    """Función principal"""
    app = MainApplication()
    app.run()

if __name__ == "__main__":
    main() 