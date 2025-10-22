import pyodbc
class ConexionBD:
    def _init_(self):
        self.conexion=''
    
    def establecerConexionBD(self):
        try:
            self.conexion= pyodbc.connect(
                'DRIVER={PostgreSQL Unicode};'
                'SERVER=localhost;'
                'DATABASE=safegate;'
                'Trusted_Connection=yes;'
                "PWD=Jarojmro7;"
            )
            print("Conexion exitosa")
        except Exception as ex:
            print("Error al conectar a la base de datos: " + str(ex))
    def cerrarConexionBD(self):
        self.conexion.close()