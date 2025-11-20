# main.py

import sys
from PyQt5 import QtWidgets
# Importamos la clase de la ventana de Login
from load.load_ui_reconocimiento import LoginWindow 
from controlador.file_manager import clean_temp_files
## 1. Función para cargar el archivo QSS

def cargar_estilo_qss(app, filename='style.qss'):
    """
    Carga el archivo de estilos QSS y lo aplica a la aplicación.
    """
    try:
        with open(filename, 'r') as f:
            _style = f.read()
        app.setStyleSheet(_style)
        print("Estilo QSS cargado correctamente.")
    except FileNotFoundError:
        print(f"ADVERTENCIA: Archivo de estilo '{filename}' no encontrado. Usando estilo nativo.")

## 2. Función principal que ejecuta la aplicación
if __name__ == '__main__':

    clean_temp_files()
    
    # Crea el objeto de aplicación
    app = QtWidgets.QApplication(sys.argv)
    
    # Aplica el estilo QSS
    cargar_estilo_qss(app) 
    
    # Inicia la ventana de login
    login_window = LoginWindow()
    login_window.show()
    
    # Ejecuta el loop principal de la aplicación
    sys.exit(app.exec_())