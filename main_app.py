#!/usr/bin/env python3
"""
CHINO - Aplicación de Puertos COM Virtuales
Parte 1: Verificar com0com y crear puertos
Parte 2: Escuchar JSONs desde puertos COM
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import serial
import threading
import webbrowser
import os
from datetime import datetime
from com0com_manager import Com0comManager

class CHINOApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CHINO - Puertos COM Virtuales")
        self.root.geometry("900x600")
        
        # Variables
        self.com_manager = Com0comManager()
        self.serial_port = None
        self.is_listening = False
        self.message_count = 0
        
        # Crear interfaz
        self.create_widgets()
        
        # Inicializar
        self.check_com0com()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="🔧 CHINO - Puertos COM Virtuales", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Frame de estado y acciones
        status_frame = ttk.LabelFrame(main_frame, text="Estado y Acciones", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Estado de com0com
        ttk.Label(status_frame, text="Com0com:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.com0com_status = tk.StringVar(value="⏳ Verificando...")
        com0com_label = ttk.Label(status_frame, textvariable=self.com0com_status, 
                                 font=("Arial", 10, "bold"))
        com0com_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Botón descargar com0com
        self.install_btn = ttk.Button(status_frame, text="📥 Descargar Com0com", 
                                     command=self.download_com0com, state="disabled")
        self.install_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Estado de puertos
        ttk.Label(status_frame, text="Puertos:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.ports_status = tk.StringVar(value="⏳ Verificando...")
        ports_label = ttk.Label(status_frame, textvariable=self.ports_status, 
                               font=("Arial", 10, "bold"))
        ports_label.grid(row=1, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Botón crear puertos
        self.create_ports_btn = ttk.Button(status_frame, text="🔧 Crear Puertos", 
                                          command=self.create_ports, state="disabled")
        self.create_ports_btn.grid(row=1, column=2, padx=(0, 10), pady=(10, 0))
        
        # Frame de escucha
        listener_frame = ttk.LabelFrame(main_frame, text="Escucha de JSONs", padding="10")
        listener_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        listener_frame.columnconfigure(0, weight=1)
        listener_frame.rowconfigure(1, weight=1)
        
        # Configuración de escucha
        config_frame = ttk.Frame(listener_frame)
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(config_frame, text="Puerto:").pack(side=tk.LEFT, padx=(0, 5))
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(config_frame, textvariable=self.port_var, 
                                      state="readonly", width=10)
        self.port_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        self.connect_btn = ttk.Button(config_frame, text="🔌 Conectar", 
                                     command=self.toggle_connection, state="disabled")
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.connection_status = tk.StringVar(value="❌ Desconectado")
        status_label = ttk.Label(config_frame, textvariable=self.connection_status, 
                                font=("Arial", 10, "bold"), foreground="red")
        status_label.pack(side=tk.LEFT)
        
        # Área de texto
        self.text_area = scrolledtext.ScrolledText(listener_frame, font=("Consolas", 10))
        self.text_area.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Controles
        control_frame = ttk.Frame(listener_frame)
        control_frame.grid(row=2, column=0, pady=(10, 0))
        
        clear_btn = ttk.Button(control_frame, text="🗑️ Limpiar", command=self.clear_text)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.counter_var = tk.StringVar(value="Mensajes: 0")
        counter_label = ttk.Label(control_frame, textvariable=self.counter_var)
        counter_label.pack(side=tk.LEFT)
        
    def check_com0com(self):
        """Verificar si com0com está instalado"""
        if self.com_manager.is_installed():
            self.com0com_status.set("✅ Instalado")
            self.install_btn.config(state="disabled")
            self.create_ports_btn.config(state="normal")
            self.log_message("✅ Com0com detectado correctamente")
            self.check_existing_ports()
        else:
            self.com0com_status.set("❌ No instalado")
            self.install_btn.config(state="normal")
            self.create_ports_btn.config(state="disabled")
            self.log_message("❌ Com0com no está instalado")
    
    def check_existing_ports(self):
        """Verificar puertos existentes"""
        try:
            config = self.com_manager._load_ports_config()
            ports = config.get('ports', [])
            
            if len(ports) >= 2:
                if self.com_manager._ports_exist_and_available(ports[0], ports[1]):
                    self.ports_status.set(f"✅ {ports[0]}, {ports[1]}")
                    self.port_combo['values'] = ports
                    if ports:
                        self.port_combo.set(ports[0])
                    self.connect_btn.config(state="normal")
                    self.log_message(f"✅ Puertos existentes: {ports[0]}, {ports[1]}")
                else:
                    self.ports_status.set("⚠️ No disponibles")
                    self.log_message("⚠️ Puertos guardados no están disponibles")
            else:
                self.ports_status.set("❌ No creados")
                self.log_message("📁 No hay puertos configurados")
                
        except Exception as e:
            self.ports_status.set("❌ Error")
            self.log_message(f"❌ Error al verificar puertos: {e}")
    
    def download_com0com(self):
        """Abrir página de descarga de com0com"""
        url = "https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/powersdr-iq/setup_com0com_W7_x64_signed.exe"
        
        result = messagebox.askyesno(
            "Descargar Com0com",
            "¿Deseas abrir la página de descarga de Com0com?\n\n"
            "Se abrirá tu navegador web con el enlace de descarga.\n"
            "Después de descargar e instalar, vuelve a esta aplicación."
        )
        
        if result:
            try:
                webbrowser.open(url)
                self.log_message("🌐 Abriendo página de descarga de Com0com")
            except Exception as e:
                self.log_message(f"❌ Error al abrir navegador: {e}")
    
    def create_ports(self):
        """Crear puertos COM virtuales"""
        self.log_message("🔧 Creando puertos COM...")
        
        try:
            com1, com2 = self.com_manager.create_auto_paired_ports()
            
            if com1 and com2:
                if self.com_manager._save_ports_config(com1, com2):
                    self.log_message(f"✅ Puertos creados: {com1}, {com2}")
                    
                    # Actualizar interfaz
                    self.port_combo['values'] = [com1, com2]
                    self.port_combo.set(com1)
                    self.connect_btn.config(state="normal")
                    self.ports_status.set(f"✅ {com1}, {com2}")
                    
                    messagebox.showinfo(
                        "Puertos Creados",
                        f"Puertos COM creados exitosamente:\n\n"
                        f"Puerto 1: {com1}\n"
                        f"Puerto 2: {com2}\n\n"
                        f"Configuración:\n"
                        f"• Baudrate: 115200\n"
                        f"• Use Ports Class: Activado"
                    )
                else:
                    self.log_message("⚠️ Puertos creados pero error al guardar configuración")
            else:
                self.log_message("❌ Error al crear puertos")
                messagebox.showerror("Error", "No se pudieron crear los puertos COM")
                
        except Exception as e:
            self.log_message(f"❌ Error inesperado: {e}")
            messagebox.showerror("Error", f"Error inesperado: {e}")
    
    def toggle_connection(self):
        """Conectar/desconectar del puerto COM"""
        if not self.is_listening:
            self.connect_to_port()
        else:
            self.disconnect_from_port()
    
    def connect_to_port(self):
        """Conectar al puerto COM seleccionado"""
        port = self.port_var.get()
        if not port:
            self.log_message("❌ Selecciona un puerto COM")
            return
        
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            self.is_listening = True
            self.connect_btn.config(text="🔌 Desconectar")
            self.connection_status.set("✅ Conectado")
            
            self.listen_thread = threading.Thread(target=self.listen_for_data, daemon=True)
            self.listen_thread.start()
            
            self.log_message(f"🔌 Conectado a {port}")
            
        except Exception as e:
            self.log_message(f"❌ Error al conectar a {port}: {e}")
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a {port}:\n{e}")
    
    def disconnect_from_port(self):
        """Desconectar del puerto COM"""
        self.is_listening = False
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        
        self.connect_btn.config(text="🔌 Conectar")
        self.connection_status.set("❌ Desconectado")
        self.log_message("🔌 Desconectado")
    
    def listen_for_data(self):
        """Escuchar datos del puerto COM"""
        buffer = ""
        
        while self.is_listening and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    # Buscar JSONs completos
                    while True:
                        start = buffer.find('{')
                        if start == -1:
                            break
                        
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
                            json_str = buffer[start:end]
                            buffer = buffer[end:]
                            self.process_json(json_str)
                        else:
                            break
                            
            except Exception as e:
                self.log_message(f"❌ Error al leer datos: {e}")
                break
        
        self.log_message("🔌 Thread de escucha terminado")
    
    def process_json(self, json_str):
        """Procesar JSON recibido"""
        try:
            json_data = json.loads(json_str)
            self.message_count += 1
            self.root.after(0, self.display_json, json_str, json_data)
        except json.JSONDecodeError as e:
            self.log_message(f"⚠️ JSON inválido: {e}")
    
    def display_json(self, json_str, json_data):
        """Mostrar JSON en la interfaz"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        self.text_area.insert(tk.END, f"\n{'='*60}\n")
        self.text_area.insert(tk.END, f"📨 Mensaje #{self.message_count} - {timestamp}\n")
        self.text_area.insert(tk.END, f"{formatted_json}\n")
        self.text_area.insert(tk.END, f"{'='*60}\n")
        
        self.text_area.see(tk.END)
        self.counter_var.set(f"Mensajes: {self.message_count}")
    
    def log_message(self, message):
        """Agregar mensaje de log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
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
            self.disconnect_from_port()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = CHINOApp(root)
    
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