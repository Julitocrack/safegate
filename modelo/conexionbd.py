import pyodbc

try:
    # Cadena de conexión
    conexion = pyodbc.connect(
        "DRIVER={PostgreSQL Unicode};"
        "SERVER=localhost;"
        "PORT=5432;"
        "DATABASE=safegate;"
        "UID=postgres;"
        "PWD=Jarojmro7;"
    )

    print("✅ Conexión exitosa a PostgreSQL")

except Exception as e:
    print("❌ Error al conectar:", e)

finally:
    if 'conexion' in locals():
        conexion.close()
        print("🔒 Conexión cerrada")