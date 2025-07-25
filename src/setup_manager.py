#!/usr/bin/env python3
"""
Gestor de configuración inicial para la aplicación
Verifica com0com, muestra diálogos de descarga y configura puertos COM
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os
import sys
import json
import time
import logging
import ctypes
from datetime import datetime

# Agregar el directorio src al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from com0com_manager import Com0comManager

# Configurar logging para setup manager
def setup_setup_logging():
    """Configura el sistema de logging para el setup manager"""
    logger = logging.getLogger('SetupManager')
    logger.setLevel(logging.INFO)
    
    # Evitar duplicar handlers
    if not logger.handlers:
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(console_handler)
    
    return logger

setup_logger = setup_setup_logging()

def verify_admin_privileges():
    """
    Verifica que la aplicación tenga permisos de administrador
    Esta función se ejecuta antes de cualquier operación del setup
    """
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            setup_logger.critical("❌ PERMISOS DE ADMINISTRADOR REQUERIDOS")
            
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
            sys.exit(1)
        
        setup_logger.info("✅ Permisos de administrador verificados correctamente")
        return True
        
    except Exception as e:
        setup_logger.error(f"❌ Error al verificar permisos de administrador: {e}")
        messagebox.showerror("Error", f"Error al verificar permisos de administrador: {e}")
        sys.exit(1)

class SetupManager:
    def __init__(self):
        # Verificar permisos de administrador ANTES de cualquier operación
        verify_admin_privileges()
        
        self.config_file = os.path.join("config", "com_ports_config.json")
        self.manager = Com0comManager(self.config_file)
        setup_logger.info("🔧 SetupManager inicializado")
        
    def run_initial_setup(self):
        """
        Ejecuta la configuración inicial completa con diálogos secuenciales
        Returns:
            bool: True si el setup fue exitoso, False si hay errores
        """
        setup_logger.info("🚀 Iniciando configuración inicial secuencial...")
        
        # 1. Verificar si com0com está instalado
        setup_logger.info("📋 Paso 1: Verificando instalación de Com0com...")
        if not self.check_com0com_installation():
            setup_logger.error("❌ Setup falló: Com0com no está disponible")
            return False
        
        # Pausa para que el usuario lea el mensaje
        time.sleep(1)
        
        # 2. Verificar si ya hay puertos configurados
        setup_logger.info("📋 Paso 2: Verificando puertos existentes...")
        if self.check_existing_ports():
            setup_logger.info("✅ Puertos ya configurados, setup completado")
            messagebox.showinfo("Setup Completado", 
                              "✅ Los puertos COM ya están configurados.\n\n"
                              "La aplicación está lista para usar.")
            return True
        
        # Pausa para que el usuario lea el mensaje
        time.sleep(1)
        
        # 3. Crear puertos COM
        setup_logger.info("📋 Paso 3: Creando nuevos puertos COM...")
        if not self.create_com_ports():
            setup_logger.error("❌ Setup falló: No se pudieron crear los puertos")
            return False
        
        setup_logger.info("✅ Configuración inicial completada exitosamente")
        messagebox.showinfo("Setup Completado", 
                          "🎉 Configuración inicial completada exitosamente.\n\n"
                          "Los puertos COM están listos para usar.")
        return True
    
    def check_com0com_installation(self):
        """
        Verifica si com0com está instalado
        Muestra diálogo de descarga si no lo está
        """
        if self.manager.is_installed():
            setup_logger.info("✅ Com0com detectado correctamente")
            # Mostrar mensaje de confirmación y esperar
            result = messagebox.showinfo("Com0com Detectado", 
                              "✅ Com0com está instalado correctamente.\n\n"
                              "Continuando con la configuración de puertos COM...")
            return True
        
        # Com0com no está instalado, mostrar diálogo
        setup_logger.warning("❌ Com0com no está instalado")
        
        # Crear ventana de diálogo
        dialog = tk.Tk()
        dialog.title("Com0com Requerido")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        
        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"500x300+{x}+{y}")
        
        # Configurar como ventana modal
        dialog.transient()
        dialog.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="🔧 Com0com Requerido", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Mensaje
        message_text = """Esta aplicación requiere Com0com para crear puertos COM virtuales.

Com0com es un driver gratuito que permite crear pares de puertos COM virtuales conectados entre sí.

¿Deseas descargar e instalar Com0com ahora?"""
        
        message_label = ttk.Label(main_frame, text=message_text, 
                                 wraplength=450, justify=tk.CENTER)
        message_label.pack(pady=(0, 20))
        
        # Frame de botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(0, 10))
        
        # Variables para el resultado
        result = {"action": None}
        
        def download_com0com():
            result["action"] = "download"
            dialog.destroy()
        
        def cancel_setup():
            result["action"] = "cancel"
            dialog.destroy()
        
        # Botones
        download_btn = ttk.Button(button_frame, text="📥 Descargar Com0com", 
                                 command=download_com0com, style="Accent.TButton")
        download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = ttk.Button(button_frame, text="❌ Cancelar", 
                               command=cancel_setup)
        cancel_btn.pack(side=tk.LEFT)
        
        # Estilo para botón principal
        style = ttk.Style()
        style.configure("Accent.TButton", background="#0078d4", foreground="white")
        
        # Esperar respuesta del usuario
        dialog.wait_window()
        
        if result["action"] == "download":
            # Abrir navegador con link de descarga
            download_url = "https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/powersdr-iq/setup_com0com_W7_x64_signed.exe"
            
            try:
                webbrowser.open(download_url)
                setup_logger.info("🌐 Abriendo página de descarga de Com0com")
                messagebox.showinfo("Descarga Iniciada", 
                                  "Se ha abierto el navegador con la descarga de Com0com.\n\n"
                                  "Por favor:\n"
                                  "1. Descarga e instala Com0com\n"
                                  "2. Reinicia esta aplicación\n"
                                  "3. El setup continuará automáticamente")
            except Exception as e:
                setup_logger.error(f"❌ Error al abrir navegador: {e}")
                messagebox.showerror("Error", f"No se pudo abrir el navegador: {e}")
            
            return False
        
        elif result["action"] == "cancel":
            setup_logger.warning("❌ Setup cancelado por el usuario")
            messagebox.showwarning("Setup Cancelado", 
                                 "La aplicación no puede funcionar sin Com0com.\n"
                                 "Puedes ejecutar el setup nuevamente más tarde.")
            return False
        
        return False
    
    def check_existing_ports(self):
        """
        Verifica si ya existen puertos configurados en el archivo JSON
        """
        try:
            if not os.path.exists(self.config_file):
                setup_logger.info("   📁 No hay archivo de configuración")
                return False
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            ports = config.get('ports', [])
            if len(ports) != 2:
                setup_logger.warning(f"   ⚠️ Configuración incompleta: {len(ports)} puertos encontrados")
                return False
            
            setup_logger.info(f"   📁 Puertos encontrados: {ports[0]} y {ports[1]}")
            setup_logger.info(f"   ✅ Configuración válida encontrada")
            return True
            
        except Exception as e:
            setup_logger.error(f"   ❌ Error al verificar puertos existentes: {e}")
            return False
    
    def create_com_ports(self):
        """
        Crea los puertos COM de forma síncrona con diálogo de progreso
        """
        # Mostrar diálogo de progreso
        progress_dialog = tk.Toplevel()
        progress_dialog.title("Creando Puertos COM")
        progress_dialog.geometry("400x150")
        progress_dialog.resizable(False, False)
        progress_dialog.transient()
        progress_dialog.grab_set()
        
        # Centrar ventana
        progress_dialog.update_idletasks()
        x = (progress_dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (progress_dialog.winfo_screenheight() // 2) - (150 // 2)
        progress_dialog.geometry(f"400x150+{x}+{y}")
        
        # Frame principal
        main_frame = ttk.Frame(progress_dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="🔧 Creando Puertos COM", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Mensaje de estado
        status_var = tk.StringVar(value="Buscando puertos disponibles...")
        status_label = ttk.Label(main_frame, textvariable=status_var)
        status_label.pack(pady=(0, 10))
        
        # Barra de progreso
        progress = ttk.Progressbar(main_frame, mode='indeterminate')
        progress.pack(fill=tk.X)
        progress.start()
        
        # Función para actualizar estado
        def update_status(message):
            status_var.set(message)
            progress_dialog.update()
        
        # Crear puertos en thread separado
        def create_ports_thread():
            try:
                update_status("Buscando puertos disponibles...")
                com1, com2 = self.manager.create_auto_paired_ports()
                
                if com1 and com2:
                    update_status("Guardando configuración...")
                    if self.manager._save_ports_config(com1, com2):
                        progress_dialog.after(0, lambda: finish_success(com1, com2))
                    else:
                        progress_dialog.after(0, lambda: finish_error("Error al guardar configuración"))
                else:
                    progress_dialog.after(0, lambda: finish_error("No se pudieron crear los puertos"))
                    
            except Exception as e:
                setup_logger.error(f"❌ Error inesperado: {e}")
                progress_dialog.after(0, lambda: finish_error(f"Error inesperado: {e}"))
        
        def finish_success(com1, com2):
            progress_dialog.destroy()
            setup_logger.info(f"✅ Puertos creados exitosamente: {com1} y {com2}")
            messagebox.showinfo("Configuración Exitosa", 
                              f"🎉 Puertos COM configurados correctamente:\n\n"
                              f"• Puerto 1: {com1}\n"
                              f"• Puerto 2: {com2}\n\n"
                              f"Los puertos están listos para usar.")
        
        def finish_error(error_msg):
            progress_dialog.destroy()
            setup_logger.error(f"❌ {error_msg}")
            messagebox.showerror("Error de Configuración", 
                               f"❌ {error_msg}\n\n"
                               f"💡 Verifica que tengas permisos de administrador.")
        
        # Iniciar thread de creación
        import threading
        thread = threading.Thread(target=create_ports_thread, daemon=True)
        thread.start()
        
        # Esperar a que termine
        thread.join()
        
        return True  # El resultado se maneja en los callbacks

def main():
    """Función de prueba del setup manager"""
    setup = SetupManager()
    success = setup.run_initial_setup()
    
    if success:
        setup_logger.info("✅ Setup completado exitosamente")
    else:
        setup_logger.error("❌ Setup falló")

if __name__ == "__main__":
    main() 