import pyodbc

class ConexionBD:
    def __init__(self):
        # 1. Llamar a establecerConexionBD en el constructor
        self.conexion = None
        self.establecerConexionBD()

    def establecerConexionBD(self):
        try:
            self.conexion = pyodbc.connect(
                'DRIVER={PostgreSQL Unicode};'
                'SERVER=localhost;'
                'DATABASE=safegate;'
                'UID=postgres;'             # <-- Usuario de PostgreSQL (Ejemplo)
                'PWD=Jarojmro7;'   # <-- Contraseña de PostgreSQL
            )
            print("Conexion exitosa")
        except Exception as ex:
            print("Error al conectar a la base de datos: " + str(ex))
            self.conexion = None # Asegurarse de que sea None si falla

    def cerrarConexionBD(self):
        if self.conexion:
            try:
                self.conexion.close()
                self.conexion = None
            except Exception as ex:
                print("Error al cerrar la conexión: " + str(ex))

    # --- NUEVOS MÉTODOS PARA INTERACTUAR CON LA BASE DE DATOS ---

    def ejecutar_consulta(self, sql_query, parametros=None, fetch_one=False):
        """
        Ejecuta una consulta SQL. Útil para INSERT, UPDATE, DELETE y SELECT genéricos.
        """
        if not self.conexion:
            print("Error: Conexión a BD no establecida.")
            return None

        try:
            cursor = self.conexion.cursor()
            
            if parametros:
                cursor.execute(sql_query, parametros)
            else:
                cursor.execute(sql_query)
            
            # Si es una consulta de selección, obtener los resultados
            if sql_query.strip().upper().startswith("SELECT"):
                if fetch_one:
                    resultado = cursor.fetchone()
                    return resultado
                else:
                    resultados = cursor.fetchall()
                    return resultados
            
            # Para operaciones de modificación (INSERT/UPDATE/DELETE), confirmar los cambios
            self.conexion.commit()
            return True # Éxito en la operación
            
        except Exception as ex:
            print("Error al ejecutar la consulta:", str(ex))
            # Opcionalmente: self.conexion.rollback() # Deshacer cambios si algo falla
            return None
        # finally: No cerramos la conexión aquí, la cerramos solo en main.py

    def obtener_nombre_usuario(self, id_reconocimiento):
        """
        Consulta el nombre de un usuario en la BD dado el ID proporcionado por el modelo de OpenCV.
        
        :param id_reconocimiento: El ID predicho por el modelo facial.
        :return: El nombre del usuario o 'DESCONOCIDO'.
        """
        # Asegúrate que 'usuarios' y 'id_reconocimiento' sean los nombres correctos de tu tabla y columna en PostgreSQL.
        sql = "SELECT nombre FROM usuarios WHERE id_reconocimiento = ?;" 
        
        # Usamos el método genérico, pidiendo solo un resultado (fetch_one=True)
        resultado = self.ejecutar_consulta(sql, (id_reconocimiento,), fetch_one=True)
        
        if resultado:
            return resultado[0] # Retorna el primer elemento (el nombre)
        
        return "DESCONOCIDO"