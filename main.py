import sys
import hashlib
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox

# Importa tu clase de conexión
from modelo.conexionbd import ConexionBD 

# --- UTILITY: Hashing de Contraseña ---
def hash_password(password):
    """Retorna la contraseña hasheada usando SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# --- 1. CLASE PARA EL DIÁLOGO DE REGISTRO (RegistroUsuarioDialog.ui) ---
class RegistroUsuarioDialog(QtWidgets.QDialog):
    def __init__(self, conexion_bd):
        super().__init__()
        # AJUSTA LA RUTA a tu archivo .ui
        uic.loadUi('ui/RegistroUsuarioDialog.ui', self) 
        self.conexion_bd = conexion_bd
        
        # <<<<<<<<<<<<<<< CÓDIGO CORREGIDO AQUÍ >>>>>>>>>>>>>>>
        # CONEXIÓN DEL BOTÓN REGISTRAR (Asume objectName='btn_registrar')
        # Si usaste un QFrame con QPushButtons, conéctalos con .clicked
        self.btn_registrar.clicked.connect(self.registrar_usuario)
        self.btn_cancelar.clicked.connect(self.reject) # Opcional: para cerrar con Cancelar
        # <<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        
        # Configurar campos y esconder error
        self.txt_contrasena.setEchoMode(QtWidgets.QLineEdit.Password)
        self.txt_confirmar_contrasena.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lbl_error_registro.setVisible(False)
        
        # NOTA: Si usaste un botón de Cancelar separado, puedes conectarlo así:
        #self.btn_cancelar.clicked.connect(self.close) 

    def registrar_usuario(self):
        # 1. OBTENER DATOS (usando los objectNames: txt_nombre, txt_usuario, etc.)
        nombre = self.txt_nombre.text().strip()
        usuario = self.txt_usuario.text().strip()
        contrasena = self.txt_contrasena.text()
        confirmar = self.txt_confirmar_contrasena.text()
        rol = self.cmb_rol.currentText() 

        # 2. VALIDACIÓN DE INTERFAZ
        if not all([nombre, usuario, contrasena, confirmar]):
            self.lbl_error_registro.setText("Error: Complete todos los campos.")
            self.lbl_error_registro.setVisible(True)
            return

        if contrasena != confirmar:
            self.lbl_error_registro.setText("Error: Las contraseñas no coinciden.")
            self.lbl_error_registro.setVisible(True)
            return
            
        self.lbl_error_registro.setVisible(False)

        # 3. LÓGICA DE INSERCIÓN EN BD
        try:
            pass_hash = hash_password(contrasena)
            
            sql = "INSERT INTO usuarios (nombre, usuario, password_hash, rol) VALUES (?, ?, ?, ?)"
            
            if self.conexion_bd.ejecutar_consulta(sql, (nombre, usuario, pass_hash, rol)):
                QMessageBox.information(self, "Éxito", f"Usuario '{usuario}' registrado. ¡Bienvenido!")
                self.accept()
            else:
                 QMessageBox.critical(self, "Error BD", "El usuario ya existe o hubo un fallo al registrar.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de Base de Datos: {e}")


# --- 2. CLASE PARA LA VENTANA DE LOGIN (LoginWindow.ui) ---
class LoginWindow(QtWidgets.QMainWindow):
    def __init__(self, conexion_bd):
        super().__init__()
        # AJUSTA LA RUTA a tu archivo .ui
        uic.loadUi('ui/LoginWindow.ui', self)
        self.conexion_bd = conexion_bd
        
        # CONEXIÓN DE EVENTOS (btn_ingresar, btn_registrar)
        self.btn_ingresar.clicked.connect(self.iniciar_sesion)
        self.btn_registrar.clicked.connect(self.abrir_registro)
        
        self.txt_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lbl_error.setVisible(False)

    def abrir_registro(self):
        """Abre la ventana de Registro."""
        dialogo_registro = RegistroUsuarioDialog(self.conexion_bd)
        dialogo_registro.exec_()
        
    def iniciar_sesion(self):
        usuario = self.txt_usuario.text().strip()
        contrasena = self.txt_pass.text()
        
        if not usuario or not contrasena:
            self.lbl_error.setText("Ingrese usuario y contraseña.")
            self.lbl_error.setVisible(True)
            return
            
        # 1. Hashear la contraseña ingresada
        pass_hash = hash_password(contrasena)

        # 2. Verificar en la BD
        rol = self.conexion_bd.verificar_login(usuario, pass_hash)
        
        if rol is None:
            self.lbl_error.setText("Usuario o contraseña incorrectos.")
            self.lbl_error.setVisible(True)
            return

        QMessageBox.information(self, "Acceso Correcto", f"Login exitoso como {rol}.")
        
        # Aquí es donde se abrirían las Main Windows (próximo paso)
        # self.main_window = GuardiaMainWindow(self.conexion_bd) 
        # self.main_window.show()
        self.close() 

# --- FUNCIÓN PRINCIPAL DE INICIO ---
def main():
    app = QtWidgets.QApplication(sys.argv)
    
    bd = ConexionBD() 
    
    if bd.conexion is None:
        QMessageBox.critical(None, "Error de Conexión", 
                             "No se pudo conectar a PostgreSQL. La aplicación no podrá funcionar.")
        # Aquí puedes decidir si salir si la BD es vital
    
    global login_window_ref
    login_window_ref = LoginWindow(bd)
    login_window_ref.show()
    
    exit_code = app.exec_()
    
    bd.cerrarConexionBD() 
    sys.exit(exit_code)

if __name__ == "__main__":
    login_window_ref = None 
    main()