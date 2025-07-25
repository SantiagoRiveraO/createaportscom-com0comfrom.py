#!/usr/bin/env python3
"""
Interfaz simple para escuchar JSONs desde puertos COM
Lee la configuración guardada y se conecta a uno de los puertos
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import serial
import threading
import time
from datetime import datetime
import os

class COMListener:
    def __init__(self, root):
        self.root = root
        self.root.title("COM Listener - Escuchando JSONs")
        self.root.geometry("800x600")
        
        # Variables
        self.serial_port = None
        self.is_listening = False
        self.config_file = "config/com_ports_config.json"
        
        # Crear interfaz
        self.create_widgets()
        
        # Cargar configuración de puertos
        self.load_ports_config()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="🔍 COM Listener - Escuchando JSONs", 
                               font=("Arial", 14, "bold"))
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
        
        # Contador de mensajes
        self.message_count = 0
        
        # Cargar configuración de puertos y conectar automáticamente
        self.load_ports_config()
    
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
    
    def on_closing(self):
        """Manejar cierre de ventana"""
        if self.is_listening:
            self.is_listening = False
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.log_message("🔌 Desconectado al cerrar aplicación")
        self.root.destroy()

def main():
    root = tk.Tk()
    app = COMListener(root)
    
    # Configurar cierre de ventana
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Centrar ventana
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main() 