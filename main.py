# main.py

# Importa la clase de conexión desde tu módulo 'modelo'
from modelo.conexionbd import ConexionBD 

# Importa la función principal de tu controlador de lógica facial.
# Asegúrate de haber creado la carpeta 'controlador' y el archivo 'controlador_facial.py'
try:
    from controlador.controlado_facial import iniciar_reconocimiento_facial
except ImportError:
    print("Error: No se pudo importar 'iniciar_reconocimiento_facial'.")
    print("Asegúrate de que la carpeta 'controlador' y el archivo 'controlador_facial.py' existan.")
    # Si no puedes importar, define una función dummy para que main.py compile temporalmente
    def iniciar_reconocimiento_facial(bd):
        print("Función de reconocimiento no cargada. Por favor, crea el archivo controlador/controlador_facial.py")


def main():
    print("--- SafeGate: Iniciando Sistema ---")
    
    # 1. Inicializar y Conectar a la Base de Datos
    # Al crear la instancia, se intenta establecer la conexión (revisar __init__ en conexionbd.py)
    bd = ConexionBD() 
    
    # Verificar si la conexión fue exitosa
    if bd.conexion is None:
        print("ADVERTENCIA: No se pudo establecer la conexión a la base de datos. El sistema operará sin acceso a datos de usuario.")
    
    # 2. Iniciar la Lógica del Reconocimiento Facial
    try:
        # Aquí se pasa la instancia de la conexión a la función de OpenCV
        print("Llamando a la función de reconocimiento facial...")
        iniciar_reconocimiento_facial(bd)
        
    except KeyboardInterrupt:
        # Permite salir limpiamente con Ctrl+C
        print("\nPrograma interrumpido por el usuario (Ctrl+C).")
    except Exception as e:
        print(f"\nFATAL ERROR: Ocurrió un error inesperado en el sistema principal: {e}")
        
    finally:
        # 3. Cerrar la conexión a la BD
        bd.cerrarConexionBD() 
        print("--- SafeGate: Conexión a BD cerrada. Sistema finalizado. ---")


if __name__ == "__main__":
    # La ejecución comienza aquí
    main()