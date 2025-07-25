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
import time
from datetime import datetime
import os
import sys
import webbrowser
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
        self.serial_port = None
        self.is_listening = False
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
        
        # Configurar icono (si existe)
        try:
            # Aquí puedes agregar un icono personalizado
            pass
        except:
            pass
        
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
        main_frame.rowconfigure(2, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="🔍 CHINO - Monitor de Puertos COM", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Frame de configuración
        config_frame = ttk.LabelFrame(main_frame, text="Estado de Conexión", padding="5")
        config_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Puerto COM
        ttk.Label(config_frame, text="Puerto COM:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(config_frame, textvariable=self.port_var, state="readonly", width=10)
        self.port_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # Estado de conexión
        self.status_var = tk.StringVar(value="⏳ Conectando...")
        status_label = ttk.Label(config_frame, textvariable=self.status_var, 
                                foreground="orange", font=("Arial", 10, "bold"))
        status_label.grid(row=0, column=2)
        
        # Cargar puertos disponibles y conectar automáticamente
        self.load_ports_config()
        
        # Área de texto para mostrar JSONs
        text_frame = ttk.LabelFrame(main_frame, text="JSONs Recibidos", padding="5")
        text_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        # Texto con scroll
        self.text_area = scrolledtext.ScrolledText(text_frame, height=20, width=80, 
                                                   font=("Consolas", 10))
        self.text_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame de controles
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))
        
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
        self.log_message("🔌 Conectando automáticamente...")
        
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
                    self.port_combo['values'] = all_ports
                    
                    # Seleccionar automáticamente el puerto de mayor número de los creados
                    # (el listener se conecta al puerto mayor, el sistema externo al menor)
                    port1, port2 = created_ports[0], created_ports[1]
                    
                    # Extraer números de puerto (ej: "COM10" -> 10)
                    try:
                        num1 = int(port1[3:])  # Extraer número después de "COM"
                        num2 = int(port2[3:])  # Extraer número después de "COM"
                        
                        # Seleccionar el puerto de mayor número de los creados
                        if num2 > num1:
                            default_port = port2  # Puerto mayor
                            self.log_message(f"📡 Puerto por defecto: {port2} (mayor de los creados)")
                            self.log_message(f"📡 Sistema externo debe conectar a {port1} (menor de los creados)")
                        else:
                            default_port = port1  # Puerto mayor
                            self.log_message(f"📡 Puerto por defecto: {port1} (mayor de los creados)")
                            self.log_message(f"📡 Sistema externo debe conectar a {port2} (menor de los creados)")
                        
                        self.port_combo.set(default_port)
                        
                        # Conectar automáticamente al puerto por defecto
                        self.connect_to_port_auto(default_port)
                        
                    except ValueError:
                        # Si no se pueden extraer números, usar el segundo puerto por defecto
                        self.port_combo.set(port2)
                        self.log_message(f"📡 Puerto por defecto: {port2}")
                        # Conectar automáticamente
                        self.connect_to_port_auto(port2)
                    
                    self.log_message(f"📁 Puertos creados: {port1} y {port2}")
                    self.log_message(f"📋 Puertos disponibles en el sistema: {len(all_ports)} puertos")
                    
                    # Configurar evento para cambiar puerto
                    self.port_combo.bind('<<ComboboxSelected>>', self.on_port_changed)
                    
                else:
                    self.log_message("⚠️ No hay puertos configurados en el JSON")
                    if all_ports:
                        # Si no hay configuración, usar el primer puerto disponible
                        self.port_combo['values'] = all_ports
                        self.port_combo.set(all_ports[0])
                        self.log_message(f"📋 Usando primer puerto disponible: {all_ports[0]}")
                        self.connect_to_port_auto(all_ports[0])
                        self.port_combo.bind('<<ComboboxSelected>>', self.on_port_changed)
            else:
                self.log_message("❌ Archivo de configuración no encontrado")
                if all_ports:
                    # Si no hay configuración, usar el primer puerto disponible
                    self.port_combo['values'] = all_ports
                    self.port_combo.set(all_ports[0])
                    self.log_message(f"📋 Usando primer puerto disponible: {all_ports[0]}")
                    self.connect_to_port_auto(all_ports[0])
                    self.port_combo.bind('<<ComboboxSelected>>', self.on_port_changed)
        except Exception as e:
            self.log_message(f"❌ Error al cargar configuración: {e}")
    
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
    
    def on_port_changed(self, event):
        """Manejar cambio de puerto seleccionado"""
        new_port = self.port_var.get()
        if new_port and new_port != getattr(self, 'current_port', None):
            self.log_message(f"🔄 Cambiando a puerto: {new_port}")
            
            # Desconectar del puerto actual
            if self.is_listening:
                self.is_listening = False
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.close()
                self.log_message("🔌 Desconectado del puerto anterior")
            
            # Conectar al nuevo puerto
            self.connect_to_port_auto(new_port)
            self.current_port = new_port
    
    def connect_to_port_auto(self, port):
        """Conectar automáticamente al puerto COM seleccionado"""
        if not port:
            self.log_message("❌ No hay puerto disponible para conectar")
            self.status_var.set("❌ Error")
            return
        
        try:
            # Configurar puerto serial
            self.serial_port = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            self.is_listening = True
            self.status_var.set("✅ Conectado")
            
            # Iniciar thread de escucha
            self.listen_thread = threading.Thread(target=self.listen_for_data, daemon=True)
            self.listen_thread.start()
            
            self.log_message(f"🔌 Conectado automáticamente a {port}")
            self.log_message("📡 Esperando datos JSON...")
            
        except Exception as e:
            self.log_message(f"❌ Error al conectar automáticamente a {port}: {e}")
            self.status_var.set("❌ Error de conexión")
    
    def listen_for_data(self):
        """Escuchar datos del puerto COM en un thread separado"""
        buffer = ""
        
        while self.is_listening and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    # Buscar JSONs completos
                    while True:
                        # Buscar inicio de JSON
                        start = buffer.find('{')
                        if start == -1:
                            break
                        
                        # Buscar fin de JSON
                        brace_count = 0
                        end = -1
                        
                        for i in range(start, len(buffer)):
                            if buffer[i] == '{':
                                brace_count += 1
                            elif buffer[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end = i + 1
                                    break
                        
                        if end > start:
                            # Extraer JSON completo
                            json_str = buffer[start:end]
                            buffer = buffer[end:]
                            
                            # Procesar JSON
                            self.process_json(json_str)
                        else:
                            # JSON incompleto, esperar más datos
                            break
                            
            except Exception as e:
                self.log_message(f"❌ Error al leer datos: {e}")
                break
        
        self.log_message("🔌 Thread de escucha terminado")
    
    def process_json(self, json_str):
        """Procesar JSON recibido"""
        try:
            # Intentar parsear JSON
            json_data = json.loads(json_str)
            
            # Incrementar contador
            self.message_count += 1
            
            # Mostrar en interfaz (usar after para thread safety)
            self.root.after(0, self.display_json, json_str, json_data)
            
        except json.JSONDecodeError as e:
            self.log_message(f"⚠️ JSON inválido: {e}")
            self.log_message(f"   Datos: {json_str[:100]}...")
    
    def display_json(self, json_str, json_data):
        """Mostrar JSON en la interfaz"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Formatear JSON para mostrar
        formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        # Agregar al área de texto
        self.text_area.insert(tk.END, f"\n{'='*60}\n")
        self.text_area.insert(tk.END, f"📨 Mensaje #{self.message_count} - {timestamp}\n")
        self.text_area.insert(tk.END, f"{formatted_json}\n")
        self.text_area.insert(tk.END, f"{'='*60}\n")
        
        # Scroll al final
        self.text_area.see(tk.END)
        
        # Actualizar contador
        self.counter_var.set(f"Mensajes: {self.message_count}")
    
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
    
    def reconnect(self):
        """Reconectar al puerto COM actual"""
        if self.is_listening:
            # Desconectar primero
            self.is_listening = False
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.log_message("🔌 Desconectado para reconectar")
        
        # Obtener puerto actual
        port = self.port_var.get()
        if port:
            self.status_var.set("⏳ Reconectando...")
            self.log_message(f"🔄 Reconectando a {port}...")
            self.connect_to_port_auto(port)
        else:
            self.log_message("❌ No hay puerto seleccionado para reconectar")
    
    def on_closing(self):
        """Manejar cierre de ventana"""
        if self.is_listening:
            self.is_listening = False
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.log_message("🔌 Desconectado al cerrar aplicación")
        
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