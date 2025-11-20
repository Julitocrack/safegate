import cv2
from PyQt5.QtCore import QTimer
# Asegúrate de importar la clase ConexionBD
from modelo.conexionbd import ConexionBD 
import numpy as np 

class ReconocimientoFacialController:
    # Asegúrate de que este constructor tenga la misma firma que en el archivo de la UI
    def __init__(self, ui_callback): 
        self.db = ConexionBD()
        self.ui_callback = ui_callback # Referencia a la MainWindow para actualizar la UI
        self.timer = QTimer()
        self.timer.timeout.connect(self.procesar_frame_de_camara)
        
        # Intentar abrir la cámara (índice 0 es la webcam predeterminada)
        self.cap = cv2.VideoCapture(0) 
        
        # Inicializar datos biométricos y otros recursos (opcional, pero buena práctica)
        self.plantillas_cargadas = {} 
        self.cargar_datos_biometricos() 
        
        # Si la cámara abre, la iniciamos de inmediato
        if self.cap.isOpened():
             self.iniciar_video()


    def cargar_datos_biometricos(self):
        # Implementación simple para evitar errores, si la DB no tiene datos aún
        datos = self.db.obtener_plantillas_biometricas() 
        for usuario_id, plantilla_bytes in datos:
            self.plantillas_cargadas[usuario_id] = plantilla_bytes 
        print(f"Plantillas cargadas: {len(self.plantillas_cargadas)}")


    def iniciar_video(self):
        if self.cap.isOpened():
            # Inicia el temporizador para leer frames a ~30 FPS
            self.timer.start(33) 
            print("Video stream iniciado.")
        else:
            print("ERROR: No se pudo acceder a la cámara.")


    def detener_video(self):
        self.timer.stop()
        if self.cap.isOpened():
            self.cap.release()
            print("Video stream detenido y cámara liberada.")


    def procesar_frame_de_camara(self):
        """Captura un frame, lo procesa (reconocimiento/simulación) y lo envía a la UI."""
        ret, frame = self.cap.read()
        
        if ret:
            # --- Lógica de Simulación de Reconocimiento y Registro ---
            # Por ahora, solo simula el estado para no depender del motor real.
            usuario_id, estado_acceso, mensaje_ui = self.simular_reconocimiento(frame)
            
            # Registrar acceso en la base de datos (Bitácora)
            if estado_acceso in ['Concedido', 'Denegado']:
                 self.db.registrar_acceso_automatico(usuario_id, estado_acceso)
                 # self.ui_callback.actualizar_bitacora_reciente() # Descomentar cuando implementes la bitácora
            
            # Dibujar el estado en el frame
            frame_procesado = self.dibujar_info(frame, estado_acceso, mensaje_ui)
            
            # 4. Enviar el frame a la MainWindow para su visualización
            self.ui_callback.mostrar_frame(frame_procesado)


    # --- Métodos Auxiliares (Simulación) ---
    def simular_reconocimiento(self, frame):
        # Lógica de prueba: siempre devuelve Concedido para un ID de prueba
        if len(self.plantillas_cargadas) > 0:
            return list(self.plantillas_cargadas.keys())[0], 'Concedido', 'ACCESO CONCEDIDO (Prueba)'
        else:
            return None, 'Denegado', 'Buscando rostro...'

    def dibujar_info(self, frame, estado, mensaje):
        color = (0, 0, 255) if estado == 'Denegado' else (0, 255, 0)
        cv2.putText(frame, mensaje, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
        return frame