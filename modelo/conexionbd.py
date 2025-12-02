import psycopg2
from psycopg2 import OperationalError, DatabaseError
from psycopg2 import sql

class ConexionBD:
    """
    Clase para manejar la conexión a una base de datos PostgreSQL usando psycopg2.
    Incluye métodos para la autenticación de guardias y el registro de accesos.
    """
    def __init__(self):
        self.conexion = None
        self.establecerConexionBD()

    def establecerConexionBD(self):
        # 📚 Parámetros de conexión para PostgreSQL
        # *** DEBES AJUSTAR ESTOS VALORES A TU ENTORNO ***
        dbname = "safegate"
        user = "postgres"
        password = "1234" 
        host = "localhost"
        port = "5432"

        try:
            self.conexion = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            self.conexion.autocommit = False
            print("✅ Conexión exitosa a la base de datos PostgreSQL.")
        
        except (OperationalError, DatabaseError) as ex:
            print("❌ Error al conectar a la base de datos:")
            print(f"Detalle del error: {ex}")
            self.conexion = None
        except Exception as ex:
            print("❌ Error inesperado durante la conexión:")
            print(f"Detalle del error: {ex}")
            self.conexion = None

    def cerrarConexionBD(self):
        """Cierra la conexión si está abierta."""
        if self.conexion:
            self.conexion.close()
            self.conexion = None
            print("➡️ Conexión a la base de datos cerrada.")

    # --- MÉTODOS DE LOGIN Y UTILERÍA ---
    
    def verificar_fraccionamiento(self, nombre_fraccionamiento):
        """Verifica que el fraccionamiento exista y esté activo."""
        if not self.conexion: return False
        try:
            with self.conexion.cursor() as cur:
                sql_query = """
                    SELECT COUNT(*)
                    FROM "administracion".fraccionamientos
                    WHERE nombre = %s AND estado = TRUE;
                """
                cur.execute(sql_query, (nombre_fraccionamiento,))
                return cur.fetchone()[0] > 0
        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL al verificar fraccionamiento: {e}")
            return False

    def obtener_plantillas_biometricas(self):
        """Obtiene el ID del usuario y la plantilla biométrica."""
        if not self.conexion: return []
        try:
            with self.conexion.cursor() as cur:
                sql_query = """
                    SELECT usuario_id, plantilla_biometrica
                    FROM "administracion".usuarios
                    WHERE plantilla_biometrica IS NOT NULL;
                """
                cur.execute(sql_query)
                return cur.fetchall()
        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL al obtener plantillas: {e}")
            return []

    def autenticar_guardia(self, email_guardia, contrasena):
        """Verifica las credenciales en la tabla 'trabajadores'."""
        if not self.conexion: self.establecerConexionBD()
        if not self.conexion: return False
        
        try:
            with self.conexion.cursor() as cur:
                sql_query = """
                    SELECT hash_contrasena, rol
                    FROM "administracion".trabajadores
                    WHERE email = %s AND estado = TRUE;
                """
                cur.execute(sql_query, (email_guardia,))
                resultado = cur.fetchone()
                
                if resultado:
                    hash_almacenado = resultado[0]
                    if contrasena == hash_almacenado: # Uso de contraseña simple
                        print(f"✅ Autenticación exitosa para trabajador: {email_guardia} ({resultado[1]})")
                        return True
                    else: return False
                else: return False
        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL durante la autenticación: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado durante la autenticación: {e}")
            return False

    # --- MÉTODOS DE REGISTRO Y CONSULTA ---
    
    def obtener_bitacora_reciente(self, limite=15):
        if not self.conexion: return []
        try:
            with self.conexion.cursor() as cur:
                cur.execute("""
                    SELECT
                        ra.momento,
                        ra.estado,
                        -- Columna 3: Nombre del Colono o Visitante
                        CASE
                            WHEN ra.estado = 'Manual' THEN ra.nombre_visitante  -- <-- ¡CORREGIDO! Usamos el nuevo campo
                            WHEN ra.usuario_id IS NOT NULL THEN u.nombre_completo
                            ELSE 'N/A'
                        END AS nombre_completo,
                        -- Columna 4: Dirección de Destino (Solo para Manual)
                        ra.direccion_destino
                    FROM
                        "administracion".registros_acceso ra
                    LEFT JOIN
                        "administracion".usuarios u ON ra.usuario_id = u.usuario_id
                    WHERE
                        ra.estado IN ('Concedido', 'Manual')
                    ORDER BY
                        ra.momento DESC
                    LIMIT %s;
                """, (limite,))
                
                return cur.fetchall()
        
        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL al obtener bitácora: {e}")
            return []
        except Exception as e:
            print(f"❌ Error inesperado al obtener bitácora: {e}")
            return []

    def registrar_acceso_automatico(self, usuario_id, estado):
        """Registra un log de acceso CONCEDIDO."""
        if not self.conexion: return False
        try:
            with self.conexion.cursor() as cur:
                sql_insert = sql.SQL("""
                    INSERT INTO "administracion".registros_acceso 
                        (usuario_id, estado)
                    VALUES (%s, %s);
                """)
                cur.execute(sql_insert, (usuario_id, estado))
                self.conexion.commit()
                print(f"✅ Acceso automático registrado. Estado: {estado}. Usuario ID: {usuario_id or 'N/A'}")
                return True
        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL al registrar acceso automático: {e}")
            self.conexion.rollback()
            return False

    def registrar_visita_manual(self, nombre_visitante, placas, direccion, foto_url=None):
        if not self.conexion: 
            self.establecerConexionBD()
            if not self.conexion: return False

        try:
            with self.conexion.cursor() as cur:
                # --- NUEVO INSERT SQL (Incluye la nueva columna nombre_visitante) ---
                sql_insert = sql.SQL("""
                    INSERT INTO "administracion".registros_acceso 
                        (usuario_id, estado, nombre_visitante, direccion_destino, foto_id_url)
                    VALUES (%s, %s, %s, %s, %s);
                """)
                
                detalle_placas = f"(Placas: {placas if placas else 'N/A'})"
                
                # ¡NUEVOS ARGUMENTOS! Ahora incluimos el nombre en su propia columna.
                args = (None, 'Manual', nombre_visitante, f"{direccion} {detalle_placas}", foto_url)
                
                cur.execute(sql_insert, args)
                self.conexion.commit()
                
                print(f"✅ Visita manual registrada: {nombre_visitante}. Destino: {direccion}")
                return True

        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL al registrar visita: {e}")
            self.conexion.rollback() 
            return False
        except Exception as e:
            print(f"❌ Error inesperado durante el registro: {e}")
            return False