import cv2
import numpy as np
import os 
from pathlib import Path

# --- CONFIGURACIÓN DE OPENCV ---
# Define la ruta al clasificador de rostros (busca en la instalación de OpenCV)
# Usamos cv2.data.haarcascades para encontrarlo automáticamente.
CASCADA_ROSTROS = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# NOTA: Debes cargar tu modelo de reconocimiento aquí una vez que lo entrenes
# Ejemplo:
# RUTA_MODELO = "modelo_entrenado.yml"
# RECONOCEDOR = cv2.face.LBPHFaceRecognizer_create()
# if Path(RUTA_MODELO).exists():
#     RECONOCEDOR.read(RUTA_MODELO)
# else:
#     print("ADVERTENCIA: Modelo de reconocimiento no encontrado. Solo se hará detección.")


def iniciar_reconocimiento_facial(conexion_bd):
    """
    Inicia la cámara, detecta rostros y realiza el reconocimiento.
    Utiliza el backend AVFoundation para mayor compatibilidad en macOS.
    
    :param conexion_bd: Instancia de la clase ConexionBD.
    """
    print("-> Iniciando reconocimiento facial con OpenCV...")

    # MEJOR OPCIÓN: Forzar el backend AVFoundation de macOS
    camara = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)  
    
    if not camara.isOpened():
        # Fallback 1: Probar el índice 1 con AVFoundation (para cámaras externas o diferentes)
        camara = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION)
        
        if not camara.isOpened():
             print("Error FATAL: No se puede abrir la cámara con AVFoundation en índices 0 ni 1.")
             return

    # Comienzo del bucle de captura de video
    while True:
        ret, frame = camara.read()
        
        if not ret:
            print("Error: Fallo al capturar frame. Terminando bucle.")
            break

        # Convertir a escala de grises para el procesamiento facial
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detectar rostros
        rostros = CASCADA_ROSTROS.detectMultiScale(
            gris,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        for (x, y, w, h) in rostros:
            # Dibujar rectángulo de detección
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # --- LÓGICA DE RECONOCIMIENTO ---
            # region_rostro = gris[y:y+h, x:x+w]
            # id_predicho, confianza = RECONOCEDOR.predict(region_rostro)
            
            # Placeholder temporal
            id_predicho = 1 
            
            # Consultar la BD (usando el método que añadimos en conexionbd.py)
            nombre = conexion_bd.obtener_nombre_usuario(id_predicho)
            
            # Mostrar el resultado
            etiqueta = f"ID: {id_predicho} | Usuario: {nombre}" 
            cv2.putText(frame, etiqueta, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)


        # Mostrar la ventana de video
        cv2.imshow('SafeGate - Reconocimiento Facial', frame)

        # Presiona 'q' para salir del programa
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Liberar la cámara y cerrar todas las ventanas de OpenCV
    camara.release()
    cv2.destroyAllWindows()
    print("-> Reconocimiento facial finalizado.")