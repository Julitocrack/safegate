# controlador/ocr_handler.py

# import pytesseract
# from PIL import Image
# import numpy as np
# import cv2 
# import os

# --- 1. CONFIGURACIÓN DE TESSERACT (CRUCIAL) ---
# Usa la ruta que Homebrew te dio para que Python encuentre el ejecutable.
# pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract' 
# -----------------------------------------------


# def procesar_imagen_y_extraer_nombre(image_path):
#     """
#     Procesa la imagen (rotación, umbral adaptativo) y usa Tesseract con una lista blanca 
#     de caracteres (whitelist) para extraer el nombre con mayor precisión.
#     """
#     try:
#         1. PRE-PROCESAMIENTO CON OPENCV
        
#         Cargar la imagen
#         img_cv = cv2.imread(image_path)
#         if img_cv is None:
#             raise ValueError(f"cv2.imread falló al leer la imagen: {image_path}")
            
#         ROTACIÓN: Asume que la cámara toma la foto en modo vertical y el ID es horizontal.
#         img_cv = cv2.rotate(img_cv, cv2.ROTATE_90_CLOCKWISE) 
        
#         Convertir a escala de grises
#         img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
#         APLICAR UMBRAL ADAPTATIVO (Mejor para IDs con sombras/brillos)
#         img_binary = cv2.adaptiveThreshold(
#             img_gray, 
#             255, 
#             cv2.ADAPTIVE_THRESH_GAUSSIAN_C, # Algoritmo de umbral
#             cv2.THRESH_BINARY, 
#             11, # Tamaño del bloque
#             2   # Constante a restar
#         )
        
#         Convertir a formato PIL para pytesseract
#         img_pil = Image.fromarray(img_binary) 

#         2. CONFIGURACIÓN DE OCR CON LISTA BLANCA DE CARACTERES
        
#         Restricción de caracteres: Solo permite letras mayúsculas, Ñ y espacios.
#         whitelist = "ABCDEFGHIJKLMNOPQRSTUVWXYZÑÁÉÍÓÚ "
        
#         config_tesseract = rf'--psm 6 -c tessedit_char_whitelist="{whitelist}"'
        
#         Extraemos el texto
#         text = pytesseract.image_to_string(img_pil, lang='spa', config=config_tesseract)
        
#         3. LÓGICA DE EXTRACCIÓN DE CAMPOS ESPECÍFICOS (INE)
        
#         nombre_completo = "NOMBRE NO ENCONTRADO"
#         Limpiamos el texto extraído y lo separamos por líneas
#         lines = [line.strip() for line in text.upper().split('\n') if line.strip()]
        
#         Buscar la posición de la etiqueta "NOMBRE"
#         start_index = -1
#         for i, line in enumerate(lines):
#             if "NOMBRE" in line:
#                 start_index = i
#                 break
        
#         if start_index != -1 and len(lines) > start_index + 1:
            
#             nombre_partes = []
            
#             Recorrer las líneas inmediatamente después de la etiqueta (hasta 3 líneas)
#             for i in range(start_index + 1, min(start_index + 4, len(lines))):
#                 parte = lines[i].strip()
#                 Solo añadimos partes que tengan longitud decente (no letras sueltas)
#                 if len(parte) > 5:
#                     nombre_partes.append(parte)
            
#             if nombre_partes:
#                 nombre_completo = " ".join(nombre_partes)
                
#         if nombre_completo == "NOMBRE NO ENCONTRADO":
#              Fallback: Usar las primeras líneas limpias si la búsqueda falló
#              nombre_completo = " ".join([l for l in lines[:3] if l]) 

#         return nombre_completo.strip(), text 

#     except Exception as e:
#         Captura cualquier fallo, ya sea de OCR o de procesamiento de imagen
#         print(f"ERROR Fatal en OCR (Revisar datos de idioma y Tesseract): {e}")
#         return "ERROR DE PROCESAMIENTO", ""