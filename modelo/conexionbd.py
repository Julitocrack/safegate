import psycopg2
from psycopg2 import OperationalError, DatabaseError
from psycopg2 import sql

class ConexionBD:
    """
    Clase para manejar la conexión a una base de datos PostgreSQL usando psycopg2.
    Incluye métodos para la autenticación de guardias y el registro de accesos.
    """
    def __init__(self):
        # Inicializa la conexión como None
        self.conexion = None
        # Llama a establecerConexionBD en el constructor
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
            self.conexion.autocommit = False # Aseguramos control manual de las transacciones
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

    # --- MÉTODOS DE LOGIN ---

    def verificar_fraccionamiento(self, nombre_fraccionamiento):
        """
        Verifica que el fraccionamiento exista en la tabla 'administracion.fraccionamientos'
        y esté activo (estado = TRUE).
        """
        if not self.conexion:
            return False

        try:
            with self.conexion.cursor() as cur:
                sql_query = """
                    SELECT COUNT(*)
                    FROM "administracion".fraccionamientos
                    WHERE nombre = %s AND estado = TRUE;
                """
                cur.execute(sql_query, (nombre_fraccionamiento,))
                conteo = cur.fetchone()[0]
                return conteo > 0

        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL al verificar fraccionamiento: {e}")
            return False
        
    def autenticar_guardia(self, email_guardia, contrasena):
        """
        Verifica las credenciales y el rol de un guardia (es_administrador = TRUE).
        """
        if not self.conexion:
            return False

        try:
            with self.conexion.cursor() as cur:
                sql_query = """
                    SELECT hash_contrasena
                    FROM "administracion".usuarios
                    WHERE email = %s AND es_administrador = TRUE;
                """
                
                cur.execute(sql_query, (email_guardia,))
                resultado = cur.fetchone()
                
                if resultado:
                    hash_almacenado = resultado[0]
                    # Aquí la verificación de contraseña. Usaríamos un hash real.
                    if contrasena == hash_almacenado:
                        return True
                    else:
                        return False
                else:
                    return False

        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL durante la autenticación: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado durante la autenticación: {e}")
            return False

    # --- MÉTODOS DE REGISTRO DE BITÁCORA ---

    def registrar_visita_manual(self, nombre_visitante, placas_vehiculo=None):
        """
        Llama al procedimiento almacenado 'administracion.registrar_acceso_manual'.
        """
        if not self.conexion:
            return False

        try:
            with self.conexion.cursor() as cur:
                call_sql = sql.SQL("CALL {}.{}(%s, %s)") \
                    .format(sql.Identifier('administracion'), 
                            sql.Identifier('registrar_acceso_manual'))
                
                args = (nombre_visitante, placas_vehiculo)
                
                cur.execute(call_sql, args)
                self.conexion.commit() # Confirma la transacción
                
                print(f"✅ Visita manual registrada: {nombre_visitante}")
                return True

        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL al registrar visita: {e}")
            self.conexion.rollback()
            return False
        except Exception as e:
            print(f"❌ Error inesperado durante el registro: {e}")
            return False

    def registrar_acceso_automatico(self, usuario_id, estado):
        """
        Registra un log de acceso (Concedido/Denegado) después del reconocimiento facial.
        """
        if not self.conexion:
            return False

        try:
            with self.conexion.cursor() as cur:
                
                sql_insert = sql.SQL("""
                    INSERT INTO "administracion".registros_acceso 
                        (usuario_id, estado)
                    VALUES (%s, %s);
                """)
                
                # psycopg2 traduce None a NULL en SQL
                args = (usuario_id, estado)
                
                cur.execute(sql_insert, args)
                self.conexion.commit()
                
                print(f"✅ Acceso automático registrado. Estado: {estado}. Usuario ID: {usuario_id or 'N/A'}")
                return True

        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL al registrar acceso automático: {e}")
            self.conexion.rollback()
            return False
        except Exception as e:
            print(f"❌ Error inesperado durante el registro automático: {e}")
            return False

    # --- OTROS MÉTODOS (Pendientes: Obtener datos biométricos) ---

    def obtener_plantillas_biometricas(self):
        """
        Obtiene el ID del usuario y la plantilla biométrica de todos los usuarios activos.
        Necesario para el motor de reconocimiento facial.
        """
        if not self.conexion:
            return []

        try:
            with self.conexion.cursor() as cur:
                sql_query = """
                    SELECT usuario_id, plantilla_biometrica
                    FROM "administracion".usuarios
                    WHERE plantilla_biometrica IS NOT NULL;
                """
                cur.execute(sql_query)
                # Devuelve una lista de tuplas [(id, plantilla_bytes), ...]
                return cur.fetchall()

        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL al obtener plantillas: {e}")
            return []
    
    def obtener_bitacora_reciente(self, limite=10):
        """
        Consulta la bitácora de accesos más recientes, incluyendo el nombre del usuario si existe.
        """
        if not self.conexion: return []
        try:
            with self.conexion.cursor() as cur:
                sql_query = """
                    SELECT ra.momento, ra.estado, COALESCE(u.nombre_completo, 'VISITA/DESCONOCIDO') AS nombre
                    FROM "administracion".registros_acceso ra
                    LEFT JOIN "administracion".usuarios u ON ra.usuario_id = u.usuario_id
                    ORDER BY ra.momento DESC
                    LIMIT %s;
                """
                cur.execute(sql_query, (limite,))
                # Devuelve [(momento, estado, nombre), ...]
                return cur.fetchall()
        except Exception as e:
            print(f"❌ Error al obtener bitácora: {e}"); return []
        
    def autenticar_guardia(self, email_guardia, contrasena):
        """
        Verifica las credenciales en la tabla 'trabajadores' y que esté activo.
        """
        if not self.conexion:
            self.establecerConexionBD()
            if not self.conexion:
                return False

        try:
            with self.conexion.cursor() as cur:
                # 1. Consulta SQL para buscar al trabajador por email y verificar que esté activo
                sql_query = """
                    SELECT hash_contrasena, rol
                    FROM "administracion".trabajadores
                    WHERE email = %s AND estado = TRUE;
                """
                
                cur.execute(sql_query, (email_guardia,))
                resultado = cur.fetchone()
                
                if resultado:
                    hash_almacenado = resultado[0]
                    rol_trabajador = resultado[1]
                    
                    # 2. Verifica la contraseña y el rol (opcionalmente)
                    if contrasena == hash_almacenado:
                        print(f"✅ Autenticación exitosa para trabajador: {email_guardia} ({rol_trabajador})")
                        return True
                    else:
                        print("❌ Contraseña incorrecta.")
                        return False
                else:
                    print("❌ Trabajador no encontrado, inactivo, o email incorrecto.")
                    return False

        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL durante la autenticación: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado durante la autenticación: {e}")
            return False
    
    def registrar_visita_manual(self, nombre_visitante, placas, direccion, foto_url=None):
        """
        Registra una visita manual con Dirección de Destino y URL de la Foto del ID.
        (Sustituye al Stored Procedure por la complejidad de los nuevos campos)
        """
        if not self.conexion:
            self.establecerConexionBD()
            if not self.conexion: return False

        try:
            with self.conexion.cursor() as cur:
                # Utilizamos INSERT directo con los nuevos campos de la tabla 'registros_acceso'
                sql_insert = sql.SQL("""
                    INSERT INTO "administracion".registros_acceso 
                        (usuario_id, estado, direccion_destino, foto_id_url)
                    VALUES (%s, %s, %s, %s);
                """)
                
                # usuario_id es NULL, estado es 'Manual'. 
                # Placas se registra en 'direccion_destino' ya que el SP original no se usa.
                # Nota: Las placas del vehículo se pueden incluir en el campo "direccion_destino" 
                # o se necesitaría otra modificación de tabla/SP para placas. Por ahora usamos Direccion + Placas.
                detalle_destino = f"{direccion} (Placas: {placas if placas else 'N/A'})"
                
                args = (None, 'Manual', detalle_destino, foto_url)
                
                cur.execute(sql_insert, args)
                self.conexion.commit()
                
                print(f"✅ Visita manual registrada. Destino: {detalle_destino}")
                return True

        except psycopg2.Error as e:
            print(f"❌ Error de PostgreSQL al registrar visita: {e}")
            self.conexion.rollback() 
            return False
        except Exception as e:
            print(f"❌ Error inesperado durante el registro: {e}")
            return False