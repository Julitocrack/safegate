# controlador/file_manager.py

import os
import time

# Definir el tiempo de vida (TTL) para las fotos temporales: 1 hora
TEMP_FILE_TTL_SECONDS = 259200 

def clean_temp_files(directory="temp_captures"):
    """
    Revisa la carpeta temporal y elimina archivos que excedan el TTL.
    """
    target_dir = os.path.join(os.getcwd(), directory)
    
    if not os.path.exists(target_dir):
        print("Gestor de Archivos: Directorio temporal no encontrado.")
        return

    now = time.time()
    count = 0

    for filename in os.listdir(target_dir):
        file_path = os.path.join(target_dir, filename)
        
        # Verificar si es un archivo y obtener su tiempo de modificación
        if os.path.isfile(file_path):
            file_mod_time = os.path.getmtime(file_path)
            
            # Si el archivo es más viejo que el TTL, bórralo
            if (now - file_mod_time) > TEMP_FILE_TTL_SECONDS:
                os.remove(file_path)
                count += 1
                
    print(f"Gestor de Archivos: Eliminados {count} archivos temporales caducados.")