# load/load_ui_reconocimiento.py

import sys
import os 
from PyQt5 import QtWidgets, uic , QtCore
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QImage, QPixmap , QColor
from PyQt5.QtCore import QTimer, Qt
import cv2 
import time
from modelo.conexionbd import ConexionBD 


# Definir la ruta base para los archivos .ui
# Esto evita problemas con rutas relativas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Clase de la Ventana Principal (MainWindow)
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, fraccionamiento):
        super().__init__()
        
        # 1. Cargar el diseño UI (Ruta robusta)
        ui_path = os.path.join(BASE_DIR, '..', 'ui', 'MainWindow.ui')
        try:
            uic.loadUi(ui_path, self) 
        except Exception as e:
            QMessageBox.critical(self, "Error Fatal de UI", f"No se pudo cargar MainWindow.ui. Error: {e}")
            sys.exit(1)

        self.setWindowTitle(f"SafeGate - Monitoreo de {fraccionamiento}")
        self.db = ConexionBD() 
        
        # 2. Inicializar el Controlador Facial (INTEGRACIÓN CRÍTICA)
        self.controller = None
        try:
            # Importamos aquí para aislar el error si falta OpenCV o si el controlador tiene un bug.
            import cv2 
            from controlador.controlado_facial import ReconocimientoFacialController
            
            self.controller = ReconocimientoFacialController(self)
            print("✅ Controlador de Reconocimiento Facial inicializado.")
            
        except ImportError as ie:
            QMessageBox.critical(self, "Error de Dependencia", 
                                 f"Falta una librería crítica (cv2 o controlador). Instale opencv-python. Error: {ie}")
            # Deshabilitar funcionalidad de video si falla
            self.video_feed_label.setText("ERROR: FALTAN DEPENDENCIAS")

        # 3. Configuración Inicial de Widgets
        self.btn_registro_manual.clicked.connect(self.abrir_registro_manual) 
        self.tabla_bitacora.setColumnCount(3)
        self.tabla_bitacora.setHorizontalHeaderLabels(['Hora', 'Estado', 'Usuario/Visitante'])
        
        if self.controller:
            self.controller.iniciar_video()

    def mostrar_frame(self, frame):
        """Convierte el frame de OpenCV a QPixmap y lo muestra en video_feed_label."""
        # Se requiere cv2 y PyQt5.QtGui (importados al inicio)
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        self.video_feed_label.setPixmap(QPixmap.fromImage(q_img).scaled(
            self.video_feed_label.size(), 
            aspectRatioMode=True 
        ))

    def closeEvent(self, event):
        """Asegura que la cámara se cierre al salir."""
        if self.controller:
            self.controller.detener_video()
        super().closeEvent(event)
    
    def abrir_registro_manual(self):
        self.manual_dialog = ManualRegisterWindow(self.db, self) # Pasa self.db y self
        self.manual_dialog.exec_()
    
    def actualizar_bitacora_reciente(self):
        """
        Consulta la DB, llena el QTableWidget (tabla_bitacora) y lo formatea.
        Ahora espera 4 columnas: momento, estado, nombre_completo, direccion_destino.
        """
        # 1. Obtener los datos de la base de datos (Ahora devuelve 4 columnas)
        datos = self.db.obtener_bitacora_reciente(limite=15)
        
        # 2. Preparar el widget
        self.tabla_bitacora.setRowCount(len(datos))
        self.tabla_bitacora.setColumnCount(3) 
        
        # 3. Iterar y llenar la tabla
        # DESEMPAQUETAR 4 VALORES: (momento, estado, nombre_completo, direccion_destino)
        for fila, (momento, estado, nombre_completo, direccion_destino) in enumerate(datos):
            
            hora_str = momento.strftime('%Y-%m-%d %H:%M:%S') 
            
            # --- LÓGICA DE COMBINACIÓN PARA LA COLUMNA FINAL ---
            if estado == 'Manual':
                # Si es manual, combinamos Nombre del Visitante y Dirección de Destino
                nombre_para_bitacora = f"{nombre_completo} -> Dir: {direccion_destino}"
                color_fondo = QColor(0, 150, 136) # Cian para Manual
            elif estado == 'Concedido':
                # Si es Concedido, solo mostramos el nombre del Colono
                nombre_para_bitacora = nombre_completo
                color_fondo = QColor(76, 175, 80) # Verde para Concedido
            else:
                # Esto es un fallback, ya que la consulta SQL filtra 'Denegado'
                nombre_para_bitacora = nombre_completo
                color_fondo = QColor(60, 60, 60) # Gris neutro
            # ----------------------------------------------------

            # Determinar el color de la fila basado en el estado (la lógica ya la tienes)
            # ... (el bloque de asignación de color fue integrado arriba para claridad)
            
            # Llenar las celdas
            items = [
                QtWidgets.QTableWidgetItem(hora_str),
                QtWidgets.QTableWidgetItem(estado),
                QtWidgets.QTableWidgetItem(nombre_para_bitacora) # Usamos la cadena combinada
            ]
            
            for col, item in enumerate(items):
                item.setBackground(color_fondo)
                item.setForeground(QColor(255, 255, 255))
                self.tabla_bitacora.setItem(fila, col, item)

        # 4. Ajustar el ancho de las columnas
        self.tabla_bitacora.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        self.tabla_bitacora.horizontalHeader().setStretchLastSection(True)

        print(f"Bitácora actualizada con {len(datos)} registros.")
        

# Clase de la Ventana de Login
class LoginWindow(QtWidgets.QDialog): 
    def __init__(self):
        super(LoginWindow, self).__init__()
        
        # Cargar el archivo .ui del Login
        ui_path = os.path.join(BASE_DIR, '..', 'ui', 'LoginWindow.ui')
        try:
            uic.loadUi(ui_path, self) 
        except Exception as e:
            QMessageBox.critical(self, "Error de UI", f"No se pudo cargar LoginWindow.ui. Error: {e}")
            sys.exit(1)

        self.db = ConexionBD() 
        self.main_window = None 
        
        self.btn_acceder.clicked.connect(self.intentar_login)
        self.txt_contrasena.setEchoMode(QtWidgets.QLineEdit.Password)
        
    def intentar_login(self):
        fraccionamiento = self.txt_fraccionamiento.text().strip()
        usuario = self.txt_usuario.text().strip()
        contrasena = self.txt_contrasena.text()

        if not fraccionamiento or not usuario or not contrasena:
            QMessageBox.warning(self, "Acceso", "Complete todos los campos.")
            return

        if not self.db.verificar_fraccionamiento(fraccionamiento):
            QMessageBox.critical(self, "Error de Acceso", f"Fraccionamiento '{fraccionamiento}' no válido o inactivo.")
            return

        if self.db.autenticar_guardia(usuario, contrasena):
            QMessageBox.information(self, "Acceso Exitoso", f"Autenticado: {usuario}")
            
            # Abrir la MainWindow
            self.main_window = MainWindow(fraccionamiento) 
            self.main_window.show()
            self.close() 
            
        else:
            QMessageBox.critical(self, "Error de Acceso", "Credenciales incorrectas o usuario no autorizado.")
    
class ManualRegisterWindow(QtWidgets.QDialog):
    def __init__(self, db_instance, parent_window):
        super().__init__(parent_window)
        
        # Carga del diseño UI
        base_path = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(base_path, '..', 'ui', 'RegistroUsuarioDialog.ui')
        uic.loadUi(ui_path, self)

        self.db = db_instance
        self.parent_window = parent_window 
        self.foto_id_capturada_url = None # Guarda la URL de la foto capturada
        
        # Conexiones de Botones (¡Asegúrate que los nombres coincidan!)
        self.btn_registrar_visita.clicked.connect(self.registrar_visita)
        self.btn_cancelar.clicked.connect(self.close)
        self.btn_escanear_id.clicked.connect(self.capturar_id)

    def capturar_id(self):
        """Abre la ventana CaptureIDWindow para escanear y procesar la foto."""
        self.capture_dialog = CaptureIDWindow(self) 
        self.capture_dialog.exec_()


    def mostrar_foto_capturada(self, ruta_archivo):
        """
        Recibe la ruta del archivo capturado y lo muestra en scan_foto_label.
        """
        from PyQt5.QtCore import Qt # Necesario para KeepAspectRatio
        
        pixmap = QPixmap(ruta_archivo)
        
        # Escala la imagen manteniendo la proporción para que quepa en el QLabel
        scaled_pixmap = pixmap.scaled(
            self.scan_foto_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        self.scan_foto_label.setPixmap(scaled_pixmap)
        self.scan_foto_label.setText("") # Elimina texto de placeholder
        self.scan_foto_label.setStyleSheet("background-color: #1a1a1a; border: 1px solid #4CAF50;") # Borde verde para confirmar


    def registrar_visita(self):
        """
        Recupera los datos de la UI y llama a la DB.
        """
        nombre = self.txt_nombre_visitante.text().strip()
        placas = self.txt_placas_vehiculo.text().strip()
        direccion = self.txt_direccion_destino.text().strip()
        
        if not direccion or not nombre:
            QMessageBox.warning(self, "Error", "El Nombre/ID y la Dirección son obligatorios.")
            return

        # Llama al método de la base de datos
        if self.db.registrar_visita_manual(nombre, placas, direccion, self.foto_id_capturada_url):
            QMessageBox.information(self, "Éxito", "Registro de visita manual completado.")
            
            # Notifica a la ventana principal para actualizar la bitácora
            self.parent_window.actualizar_bitacora_reciente() 
            
            self.close() 
        else:
            QMessageBox.critical(self, "Error DB", "Fallo al registrar. Revise la conexión.")



class CaptureIDWindow(QtWidgets.QDialog):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        
        # Cargar el diseño CaptureIDDialog.ui (Ruta robusta)
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ui', 'CaptureIDDialog.ui')
        uic.loadUi(ui_path, self) 

        self.parent_window = parent_window 
        self.current_frame = None 
        # Ruta temporal para guardar la foto capturada
        self.temp_image_path = os.path.join(os.getcwd(), "temp_id_capture.jpg") 
        
        # Inicialización de la Cámara y Timer
        self.cap = cv2.VideoCapture(0) # Abrir la cámara
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        # Conexiones:
        self.btn_tomar_foto.clicked.connect(self.tomar_foto_y_procesar)
        self.btn_cerrar.clicked.connect(self.close)
        
        if self.cap.isOpened():
            self.timer.start(50) # Iniciar el feed (20 FPS)
        else:
            self.capture_feed_label.setText("CÁMARA NO DISPONIBLE")
            self.btn_tomar_foto.setEnabled(False)


    def update_frame(self):
        """Lee un frame de la cámara y lo muestra en el QLabel."""
        ret, self.current_frame = self.cap.read()
        if ret:
            # Lógica de conversión BGR a QPixmap
            rgb_image = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            self.capture_feed_label.setPixmap(QPixmap.fromImage(q_img).scaled(
                self.capture_feed_label.size(), 
                QtCore.Qt.KeepAspectRatio, 
                QtCore.Qt.SmoothTransformation
            ))

    def tomar_foto_y_procesar(self):
        
        if self.current_frame is None:
            QMessageBox.warning(self, "Error", "No se ha capturado ningún frame.")
            return

        # 1. Crear la carpeta temporal si no existe
        capture_dir = os.path.join(os.getcwd(), "temp_captures")
        if not os.path.exists(capture_dir):
            os.makedirs(capture_dir)
            
        # 2. Generar una ruta de archivo única con un timestamp
        filename = f"id_capture_{int(time.time())}.jpg"
        self.temp_image_path = os.path.join(capture_dir, filename)
        
        # 3. Guardar el frame actual
        cv2.imwrite(self.temp_image_path, self.current_frame)
        
        # 4. Comunicar datos a la ventana de registro manual (el padre)
        self.parent_window.txt_nombre_visitante.setText("") # Deja el campo vacío para llenado manual
        self.parent_window.foto_id_capturada_url = os.path.abspath(self.temp_image_path)
        
        # 5. Mostrar la foto en el diálogo padre
        self.parent_window.mostrar_foto_capturada(os.path.abspath(self.temp_image_path)) 

        QMessageBox.information(self, "Captura", "Foto de ID guardada temporalmente.")
        self.close()

    def closeEvent(self, event):
        """Asegura que la cámara se cierre al salir."""
        self.timer.stop()
        if self.cap.isOpened():
            self.cap.release()
        super().closeEvent(event)