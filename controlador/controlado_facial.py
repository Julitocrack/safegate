# controlador/controlado_facial.py

import cv2
from PyQt5.QtCore import QTimer
from modelo.conexionbd import ConexionBD
import numpy as np
import face_recognition # La librería que acabamos de arreglar

class ReconocimientoFacialController:
    def __init__(self, ui_callback):
        self.db = ConexionBD()
        self.ui_callback = ui_callback
        self.timer = QTimer()
        self.timer.timeout.connect(self.procesar_frame_de_camara)
        
        # Listas para guardar la "memoria" del sistema
        self.known_face_encodings = [] # Los vectores matemáticos de las caras
        self.known_face_ids = []       # Los IDs de usuario correspondientes
        self.known_face_names = []     # Los nombres para mostrar en pantalla
        
        # 1. CARGA INICIAL: Traer datos de la DB y procesarlos
        self.cargar_datos_biometricos()
        
        # Iniciar cámara
        self.cap = cv2.VideoCapture(0) 
        if self.cap.isOpened():
             self.iniciar_video()

    def cargar_datos_biometricos(self):
        """
        Descarga las imágenes de la DB y genera los encodings (plantillas) 
        necesarios para la comparación.
        """
        print("🔄 Cargando rostros de la base de datos...")
        
        # Necesitamos un método en ConexionBD que traiga ID, Bytes de Foto y Nombre
        # Asumimos que obtienes: [(id, bytes, nombre), ...]
        # Si tu método 'obtener_plantillas_biometricas' solo trae 2 cosas, avísame para ajustarlo.
        # Aquí usaré una consulta directa para asegurar que traemos el nombre también.
        try:
            if not self.db.conexion: self.db.establecerConexionBD()
            with self.db.conexion.cursor() as cur:
                cur.execute("SELECT usuario_id, plantilla_biometrica, nombre_completo FROM administracion.usuarios WHERE plantilla_biometrica IS NOT NULL")
                datos = cur.fetchall()
        except Exception as e:
            print(f"❌ Error al consultar DB: {e}")
            datos = []

        count = 0
        for usuario_id, imagen_bytes, nombre in datos:
            if imagen_bytes:
                try:
                    # A. Convertir bytes (BYTEA) a imagen numpy
                    nparr = np.frombuffer(imagen_bytes, np.uint8)
                    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if img_cv is None:
                        continue

                    # B. Convertir de BGR (OpenCV) a RGB (face_recognition)
                    rgb_img = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
                    
                    # C. GENERAR LA PLANTILLA BIOMÉTRICA (Encoding)
                    # Esto busca caras en la foto guardada y saca sus medidas
                    encodings = face_recognition.face_encodings(rgb_img)
                    
                    if len(encodings) > 0:
                        # Tomamos el primer rostro encontrado en la foto de registro
                        self.known_face_encodings.append(encodings[0])
                        self.known_face_ids.append(usuario_id)
                        self.known_face_names.append(nombre)
                        count += 1
                        print(f"   -> Rostro cargado: {nombre}")
                    else:
                        print(f"   ⚠️ No se detectó cara en la foto de: {nombre}")
                        
                except Exception as e:
                    print(f"   ⚠️ Error procesando ID {usuario_id}: {e}")
        
        print(f"✅ Total: {count} rostros listos para reconocer.")

    def iniciar_video(self):
        if self.cap.isOpened():
            self.timer.start(30) # ~33 FPS

    def detener_video(self):
        self.timer.stop()
        self.cap.release()

    def procesar_frame_de_camara(self):
        ret, frame = self.cap.read()
        if not ret: return

        # --- OPTIMIZACIÓN: Reducir tamaño para velocidad ---
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        usuario_identificado = None
        estado_acceso = 'Denegado' # Por defecto
        mensaje_ui = "ESPERANDO..."
        color_ui = (0, 0, 255) # Rojo

        # 1. Detectar caras en la cámara
        face_locations = face_recognition.face_locations(rgb_small_frame)
        
        if len(face_locations) > 0:
            # 2. Calcular la plantilla biométrica de la cara actual
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                # 3. COMPARAR con la base de datos (memoria)
                # matches es una lista de True/False
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.5)
                name = "Desconocido"
                
                # Usar la distancia para encontrar el mejor candidato
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    
                    if matches[best_match_index]:
                        # --- ¡IDENTIFICADO! ---
                        name = self.known_face_names[best_match_index]
                        usuario_identificado = self.known_face_ids[best_match_index]
                        estado_acceso = 'Concedido'
                        mensaje_ui = f"ACCESO: {name}"
                        color_ui = (0, 255, 0) # Verde
                        
                        # Dibujar cuadro (ajustando la escala x4)
                        top, right, bottom, left = face_location
                        self.dibujar_cuadro(frame, top*4, right*4, bottom*4, left*4, color_ui)
                    else:
                        # Cara vista, pero no está en la base de datos
                        mensaje_ui = "NO REGISTRADO"
                        top, right, bottom, left = face_location
                        self.dibujar_cuadro(frame, top*4, right*4, bottom*4, left*4, (0, 0, 255))

        # 4. Registro en Bitácora (Solo si es Concedido para no saturar)
        # Usamos una bandera simple para no registrar 30 veces por segundo
        # (Aquí podrías agregar lógica para registrar solo 1 vez cada 5 segundos)
        if estado_acceso == 'Concedido' and usuario_identificado:
             # Opcional: Verificar cuándo fue el último registro para no spammear la DB
             self.db.registrar_acceso_automatico(usuario_identificado, estado_acceso)
             self.ui_callback.actualizar_bitacora_reciente()

        # 5. Enviar imagen a la interfaz
        frame_procesado = self.dibujar_info(frame, color_ui, mensaje_ui)
        self.ui_callback.mostrar_frame(frame_procesado)

    def dibujar_cuadro(self, frame, top, right, bottom, left, color):
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

    def dibujar_info(self, frame, color, mensaje):
        # Barra negra arriba para el texto
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 50), (0, 0, 0), -1)
        cv2.putText(frame, mensaje, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
        return frame