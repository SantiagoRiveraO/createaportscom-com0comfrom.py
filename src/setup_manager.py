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
from datetime import datetime

# Agregar el directorio src al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from com0com_manager import Com0comManager

class SetupManager:
    def __init__(self):
        self.config_file = os.path.join("config", "com_ports_config.json")
        self.manager = Com0comManager(self.config_file)
        
    def run_initial_setup(self):
        """
        Ejecuta la configuración inicial completa
        Returns:
            bool: True si el setup fue exitoso, False si hay errores
        """
        print("🚀 Iniciando configuración inicial...")
        
        # 1. Verificar si com0com está instalado
        print("📋 Paso 1: Verificando instalación de Com0com...")
        if not self.check_com0com_installation():
            print("❌ Setup falló: Com0com no está disponible")
            return False
        
        # 2. Verificar si ya hay puertos configurados
        print("📋 Paso 2: Verificando puertos existentes...")
        if self.check_existing_ports():
            print("✅ Puertos ya configurados, setup completado")
            messagebox.showinfo("Setup Completado", 
                              "✅ Los puertos COM ya están configurados.\n\n"
                              "La aplicación está lista para usar.")
            return True
        
        # 3. Crear puertos COM
        print("📋 Paso 3: Creando nuevos puertos COM...")
        if not self.create_com_ports():
            print("❌ Setup falló: No se pudieron crear los puertos")
            return False
        
        print("✅ Configuración inicial completada exitosamente")
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
            print("✅ Com0com detectado correctamente")
            # Mostrar mensaje de confirmación
            messagebox.showinfo("Com0com Detectado", 
                              "✅ Com0com está instalado correctamente.\n\n"
                              "Continuando con la configuración de puertos COM...")
            return True
        
        # Com0com no está instalado, mostrar diálogo
        print("❌ Com0com no está instalado")
        
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
                messagebox.showinfo("Descarga Iniciada", 
                                  "Se ha abierto el navegador con la descarga de Com0com.\n\n"
                                  "Por favor:\n"
                                  "1. Descarga e instala Com0com\n"
                                  "2. Reinicia esta aplicación\n"
                                  "3. El setup continuará automáticamente")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el navegador: {e}")
            
            return False
        
        elif result["action"] == "cancel":
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
                print("   📁 No hay archivo de configuración")
                return False
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            ports = config.get('ports', [])
            if len(ports) != 2:
                print(f"   ⚠️ Configuración incompleta: {len(ports)} puertos encontrados")
                return False
            
            print(f"   📁 Puertos encontrados: {ports[0]} y {ports[1]}")
            print(f"   ✅ Configuración válida encontrada")
            return True
            
        except Exception as e:
            print(f"   ❌ Error al verificar puertos existentes: {e}")
            return False
    
    def create_com_ports(self):
        """
        Crea los puertos COM de forma síncrona
        """
        # Crear puertos directamente
        print("🔍 Buscando puertos disponibles...")
        com1, com2 = self.manager.create_auto_paired_ports()
        
        if com1 and com2:
            print("💾 Guardando configuración...")
            if self.manager._save_ports_config(com1, com2):
                messagebox.showinfo("Configuración Exitosa", 
                                  f"🎉 Puertos COM configurados correctamente:\n\n"
                                  f"• Puerto 1: {com1}\n"
                                  f"• Puerto 2: {com2}\n\n"
                                  f"Los puertos están listos para usar.")
                return True
            else:
                messagebox.showerror("Error de Configuración", 
                                   "❌ Error al guardar la configuración de puertos.")
                return False
        else:
            messagebox.showerror("Error de Configuración", 
                               "❌ No se pudieron crear los puertos COM.\n\n"
                               "💡 Verifica que tengas permisos de administrador.")
            return False

def main():
    """Función de prueba del setup manager"""
    setup = SetupManager()
    success = setup.run_initial_setup()
    
    if success:
        print("✅ Setup completado exitosamente")
    else:
        print("❌ Setup falló")

if __name__ == "__main__":
    main() 