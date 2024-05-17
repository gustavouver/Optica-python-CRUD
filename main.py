'''
Programa creado por: Gustavo López P.
Usando las tecnologías:
    -Python (Versión: 3.12.1)
    -PyQt5 (Versión: 5.15.10)
    -SQLite3 (Versión: 3.41.2)
    -Conda (Versión: 23.11.0)
    -git (Version 2.43.0.windows.1)
    -ChatGPT
'''
import os
import json
import shutil
from VentanaPrincipal import Ui_MainWindow
from VentanaEdicion import Ui_Dialog
#import images.resources
#from PyQt5.uic import loadUi
# pylint: disable=no-name-in-module
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QIntValidator, QFont, QIcon
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDialog, QMessageBox,
                             QAbstractItemView, QFileDialog, QHeaderView)
#from ventana_principal import Ui_MainWindow (ventana para conectarse con la clase responsable de la parte grafica)
#from ventana_edicion import Ui_Dialog (ventana de edición de usuario)
from conexion import (create_db_connection, delete_db_connection, add_client_connection,
                      edit_client_connection, delete_client_connection)

# Clase principal que hereda de QMainWindow - Nombre de la ventana(Clase de la ventana)
class MainWindow(QMainWindow):
    """
    Clase principal:
    Esta clase extiende la funcionalidad de QMainWindow de PyQt5 
    para proporcionar una interfaz de usuario principal.
    """
    def __init__(self):
        """
        Constructor de la clase MainWindow.
        """
        super().__init__()
        self.initialize_ui()
        


    def initialize_ui(self):
        """
        Inicializa la interfaz de usuario:
        Esta función se encarga de realizar las configuraciones iniciales.
        """
        # Cargar la interfaz de usuario desde el archivo .ui
        #loadUi("VentanaPrincipal.ui", self)
        # Establece el titulo de la ventana
        
        # Ui_MainWindow es la instancia de la clase generada en VentanaPrincipal.py equivalente a: loadUi("VentanaPrincipal.ui", self)
        self.ui_ventana_principal = Ui_MainWindow()
        self.ui_ventana_principal.setupUi(self)
        self.setWindowTitle("Óptica León")
        #Se establece el icono de la aplicación
        app.setWindowIcon(QIcon("images/icons/sunglasses.ico"))
        #Pyling indica que self.db y self.model deben ser inicializados en el __init__
        self.db = None
        self.model = None
        # Carga las primera funciones vitales para el programa
        self.setup_database()
        self.setup_actions()
        self.setup_model()
        self.setup_table()
        # Configurar el QDateEdit para iniciar con la fecha actual
        self.ui_ventana_principal.in_fecha.setDate(QDate.currentDate())
        # Configura un validador de enteros para el campo de edad
        int_validator = QIntValidator()
        self.ui_ventana_principal.in_edad.setValidator(int_validator)
        # Establece el orden en el que se muestra la tabla
        self.current_order = Qt.DescendingOrder


    def get_path(self, new_db_name="Nueva base de datos"):
        """Obtiene las rutas de la base de datos, el archivo JSON y sus carpetas asociadas"""
        # Ruta del directorio actual del script
        script_directory = os.path.dirname(os.path.abspath(__file__))
        # Rutas de la carpeta y archivo JSON
        json_folder_path = os.path.join(script_directory, "json_folder")
        json_file_path = os.path.join(json_folder_path, "config.json")
        # Rutas de la carpeta y archivo de la base de datos
        db_folder_path = os.path.join(script_directory, "Base_de_datos")
        db_file_path = os.path.join(db_folder_path, new_db_name)
        return db_folder_path, db_file_path, json_folder_path, json_file_path


    def setup_database(self):
        ''' Configurar la conexión a la base de datos'''
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        _, _, _, json_file_path = self.get_path()
        # Verifica si la ruta "json_file_path" existe
        if os.path.exists(json_file_path):
            try:
                # Abre el archivo "json_file_path" en modo lectura ("r" de read)
                with open(json_file_path, "r", encoding="utf-8") as json_read:
                    json_file = json.load(json_read)
                    # Verificar si el diccionario tiene la clave "last_selected_db"
                    if "last_selected_db" in json_file:
                        last_selected_db = json_file["last_selected_db"]
                        # Se establece la conexión y etiqueta de la base de datos solo si "last_selected_db" existe y es valido
                        if last_selected_db and os.path.exists(last_selected_db):
                            self.db.setDatabaseName(last_selected_db)
                            base_name = os.path.basename(last_selected_db).replace(".db", "")
                            self.ui_ventana_principal.database_path_label.setText(base_name)
                        else:
                            # La base de datos especificada en el archivo JSON no existe o la ruta está vacía
                            self.ui_ventana_principal.database_path_label.setText("La ruta de la base de datos cambió o no existe.")
                    else:
                        # No hay información en la clave "last_selected_db" del archivo JSON
                        self.ui_ventana_principal.database_path_label.setText("No existe conexión a ninguna base de datos.")
            except json.decoder.JSONDecodeError:
                # Manejar la excepción cuando el archivo JSON existe pero está vacío
                self.ui_ventana_principal.database_path_label.setText("El archivo JSON está vacío.")
        else:
            # No existe el archivo JSON
            self.ui_ventana_principal.database_path_label.setText("No existe conexión con ninguna base de datos.")


    def setup_actions(self):
        ''' Conectar los botones y cuadros de dialogos con sus respectivas funciones'''
        self.ui_ventana_principal.btn_crear_DB.clicked.connect(self.create_db)
        self.ui_ventana_principal.btn_seleccionar_DB.clicked.connect(self.select_db)
        self.ui_ventana_principal.btn_copiar_DB.clicked.connect(self.copy_db)
        self.ui_ventana_principal.btn_eliminar_DB.clicked.connect(self.delete_db)

        self.ui_ventana_principal.btn_agregar.clicked.connect(self.add_client)
        self.ui_ventana_principal.in_nombre.returnPressed.connect(self.add_client)
        self.ui_ventana_principal.btn_editar.clicked.connect(self.edit_client)
        self.ui_ventana_principal.btn_eliminar.clicked.connect(self.delete_client)

        self.ui_ventana_principal.btn_buscar_nombre.clicked.connect(self.search_name)
        self.ui_ventana_principal.in_buscar_nombre.returnPressed.connect(self.search_name)
        self.ui_ventana_principal.btn_buscar_fecha.clicked.connect(self.search_date)

        self.ui_ventana_principal.btn_actualizar_tabla.clicked.connect(self.reset_table)
        self.ui_ventana_principal.ordenar_tabla.currentIndexChanged.connect(self.sort_box)
        self.ui_ventana_principal.btn_toggle.clicked.connect(self.toggle_order)
        self.ui_ventana_principal.btn_limpiar.clicked.connect(self.clean_data)

        self.ui_ventana_principal.btn_menu.clicked.connect(self.hide_menu)


    def setup_model(self):
        '''Establece el modelo'''
        # Crear una instancia del modelo de tabla SQL
        self.model = QSqlTableModel()
        # Selecciona la tabla a usar
        self.model.setTable("clientes")
        # Establece la columna 0 (id) como orden descendente (ultimo id agregado = primero mostrado)
        self.model.setSort(0, Qt.DescendingOrder)
        # Crear una instancia de la fuente que deseas utilizar
        font = QFont("Arial Black", 8)
        # Aplicar la fuente a la cabecera de la tabla
        self.ui_ventana_principal.tableView.horizontalHeader().setFont(font)
        # Establece el titulo de las columnas
        self.model.setHeaderData(0, Qt.Horizontal, "ID")
        self.model.setHeaderData(1, Qt.Horizontal, "Nombre")
        self.model.setHeaderData(2, Qt.Horizontal, "Edad")
        self.model.setHeaderData(3, Qt.Horizontal, "OI")
        self.model.setHeaderData(4, Qt.Horizontal, "OD")
        self.model.setHeaderData(5, Qt.Horizontal, "ADD")
        self.model.setHeaderData(6, Qt.Horizontal, "Observs")
        self.model.setHeaderData(7, Qt.Horizontal, "Fecha")
        # Establece la configuración previa del modelo
        self.model.select()


    def setup_table(self):
        '''Configura la tabla llamada "tableView" '''
        # Establecer el modelo en la tabla cuyo nombre de referencia es: "tableView"
        self.ui_ventana_principal.tableView.setModel(self.model)
        # Asegurar que la QTableView esté al frente
        self.ui_ventana_principal.tableView.raise_()
        # Establece el modo de selección de la tabla permitir selección de filas
        self.ui_ventana_principal.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # La tabla se adapta
        self.ui_ventana_principal.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Ocultar la columna 0 (columna del id)
        self.ui_ventana_principal.tableView.setColumnHidden(0, True)


    def create_db(self, new_db_name=None):
        '''Función usada para crear una nueva base de datos'''
        db_folder_path, _, _, _ = self.get_path()
        if not os.path.exists(db_folder_path):
            os.makedirs(db_folder_path)
        options = QFileDialog.Options()
        new_db_name, _ = QFileDialog.getSaveFileName(self, "Guardar Nueva Base de Datos", db_folder_path, "SQLite Database Files (*.db);;All Files (*)", options=options)
        if not new_db_name:
            return
        # Asegurarse de que la extensión .db esté presente al final
        if not new_db_name.lower().endswith(".db"):
            # Se agrega al final la extensión ".db" en caso de no existir
            new_db_name += ".db"
        # Se ejecuta la función dando como parametro el nuevo nombre
        _, db_file_path, json_folder_path, json_file_path = self.get_path(new_db_name)
        # Cerrar la conexión actual si está abierta
        if self.db.isOpen():
            self.db.close()
        try:
            # Llamar a la función para crear la nueva base de datos (en conexion.py)
            create_db_connection(db_file_path)
            # Crea la carpeta donde se ubica el archivo JSON en caso de que no exista
            if not os.path.exists(json_folder_path):
                os.makedirs(json_folder_path)
            # Abre (o crea si no existe) el archivo json en modo de escritura y escribe la ruta de la base de datos
            with open(json_file_path, "w", encoding="utf-8") as json_write:
                json_config = {"last_selected_db": db_file_path}
                json.dump(json_config, json_write)
        except RuntimeError as e:
            QMessageBox.warning(self, "Error al crear base de datos", str(e))
        except Exception as ex:
            QMessageBox.warning(self, "Error fatal al crear base de datos", f"Ocurrió un error inesperado al crear la base de datos.\n\nError: '{type(ex).__name__} - {ex}'.")
        # Establece la conexion, modelo, tabla y etiqueta de la nueva base de datos
        if not self.db.isOpen():
            self.model.clear()
            self.db.setDatabaseName(db_file_path)
            self.setup_model()
            self.setup_table()
            base_name = os.path.basename(db_file_path).replace(".db", "")
            self.ui_ventana_principal.database_path_label.setText(base_name)
            QMessageBox.information(self, "Creación exitosa", f"Se a creado exitosamente la base de datos: '<b>{base_name}</b>'.")
        else:
            QMessageBox.warning(self, "Error de conexión", "No fue posible establecer conexión con la base de datos.")


    def select_db(self):
        '''Función usada para seleccionar una nueva base de datos'''
        options_config = QFileDialog.Options()
        # El operador ' |= ' es llamado "bitwise OR" indica que el cuadro de diálogo debe abrirse en modo de solo lectura
        options_config |= QFileDialog.ReadOnly
        db_folder_path, _, json_folder_path, json_file_path = self.get_path()
        if os.path.exists(db_folder_path):
            # Seleccionar la ubicación de la base de datos que se desea cargar - getOpenFileName(parent, caption, directory, filter, options=None):
            selected_db, _ = QFileDialog.getOpenFileName(self, "Seleccionar base de datos", db_folder_path, "Archivos de base de datos (*.db);;Todos los archivos (*)", options=options_config)    
        else:
            selected_db, _ = QFileDialog.getOpenFileName(self, "Seleccionar base de datos", "", "Archivos de base de datos (*.db);;Todos los archivos (*)", options=options_config)
        try:
            if selected_db:
                self.db.close()
                self.model.clear()
                self.db.setDatabaseName(selected_db)
                self.setup_model()
                self.setup_table()
                base_name = os.path.basename(selected_db).replace(".db", "")
                self.ui_ventana_principal.database_path_label.setText(base_name)
                QMessageBox.information(self, "Selección exitosa", f"Ahora estás trabajando con la base de datos: '<b>{base_name}</b>'.")
                if not os.path.exists(json_folder_path):
                    os.makedirs(json_folder_path)
                with open(json_file_path, "w", encoding="utf-8") as json_write:
                    json_config = {"last_selected_db": selected_db}
                    json.dump(json_config, json_write)
            else:
                pass
        except Exception as ex:
            QMessageBox.warning(self, "Error fatal al seleccionar", f"Ocurrió un error inesperado al seleccionar la base de datos.\n\nError: '{type(ex).__name__} - {ex}'")


    def copy_db(self):
        '''Función usada para copiar la base de datos actual'''
        db_folder_path, _, _, json_file_path = self.get_path()
        options_config = QFileDialog.Options()
        options_config |= QFileDialog.ReadOnly
        if os.path.exists(self.db.databaseName()):
            original_name = self.ui_ventana_principal.database_path_label.text()
            default_copy_name = f"{original_name} - copia.db"
            if os.path.exists(db_folder_path):
                # Selecciona el nombre y ubicación donde se desea guardar la copia
                new_db, _ = QFileDialog.getSaveFileName(self, "Guardar copia de la base de datos", os.path.join(db_folder_path, default_copy_name), "Archivos de base de datos (*.db);; Todos los archivos (*)", options=options_config)
            else:
                new_db, _ = QFileDialog.getSaveFileName(self, "Seleccionar base de datos", default_copy_name,"Archivos de base de datos (*.db);;Todos los archivos (*)", options=options_config)
        else:
            QMessageBox.information(self, "Error al copiar", "No existe conexion con ninguna base de datos, seleccione una para copiarla.")
            return
        
        if new_db:
            try:
                # Realizar la copia de la base actual en la nueva ubicación
                shutil.copy2(self.db.databaseName(), new_db)
                # Crear un cuadro de diálogo de confirmación
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Copia de base de datos creada exitosamente")
                msg_box.setText("¿Deseas seguir trabajando con la base de datos original o con la nueva copia creada?")
                # Configurar botones del cuadro de diálogo
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)
                yes_button = msg_box.button(QMessageBox.Yes)
                yes_button.setText("Copia")
                no_button = msg_box.button(QMessageBox.No)
                no_button.setText("Original")
                choice = msg_box.exec()
                if choice == QMessageBox.Yes:
                    # El usuario elige trabajar con la copia
                    self.db.close()
                    self.model.clear()
                    self.db.setDatabaseName(new_db)
                    self.setup_model()
                    self.setup_table()
                    with open(json_file_path, "w", encoding="utf-8") as json_write:
                        json_config = {"last_selected_db": new_db}
                        json.dump(json_config, json_write)
                    base_name = os.path.basename(new_db).replace(".db", "")
                    self.ui_ventana_principal.database_path_label.setText(base_name)
                    QMessageBox.information(self, "Exito al conectar copia", f"Ahora estás trabajando con la copia llamada: '<b>{base_name}</b>'.")
                else:
                    # El usuario elige continuar con la base de datos original, no es necesario hacer nada adicional
                    pass
            except FileNotFoundError:
                QMessageBox.warning(self, "Error al copiar la base de datos", "La base de datos que deseas copiar no existe, seleccione una para copiarla.")
            except Exception as ex:
                QMessageBox.warning(self, "Error fatal al copiar la base de datos", f"Ocurrió un error inesperado al intentar copiar la base de datos.\n\nError: '{type(ex).__name__} - {ex}'")


    def delete_db(self):
        '''Función usada para eliminar la base de datos actual'''
        current_db = self.db.databaseName()
        if not os.path.exists(current_db):
            QMessageBox.warning(self, "Advertencia", "La base de datos que desea eliminar no existe.")
            return
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Eliminar base de datos")
        base_name = os.path.basename(current_db).replace(".db", "")
        msg_box.setText(f"¿Estás seguro de eliminar la base de datos actual: '<b>{base_name}</b>'?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        yes_button = msg_box.button(QMessageBox.Yes)
        yes_button.setText("Si")
        choice = msg_box.exec()
        if choice == QMessageBox.Yes:
            if self.db.isOpen():
                self.db.close()
            try:

                delete_db_connection(current_db)

                # Limpiar el modelo
                self.model.clear()
                _, _, _, json_file_path = self.get_path(current_db)
                if os.path.exists(json_file_path):
                    os.remove(json_file_path)
                self.ui_ventana_principal.database_path_label.setText("No existe conexión con ninguna base de datos.")
                QMessageBox.information(self, "Éxito", f"La base de datos '<b>{base_name}</b>' fue eliminada correctamente.")
            except RuntimeError as e:
                QMessageBox.warning(self, "Error al eliminar la base de datos", str(e))
            except Exception as ex:
                QMessageBox.warning(self, "Error fatal al eliminar la base de datos", f"Ocurrió un error inesperado al intentar eliminar la base de datos.\n\nError: '{type(ex).__name__}:  {str(ex)}'")
        else:
            return


    def show_db_dialog(self):
        '''Función usada para preguntar al usuario si desea crear o seleccionar una base de datos'''
        if not os.path.exists(self.db.databaseName()):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Base de Datos")
            msg_box.setText("No se encontró una base de datos.\n¿Desea crear o seleccionar una nueva base de datos?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Yes)
            yes_button = msg_box.button(QMessageBox.Yes)
            yes_button.setText("Crear")
            no_button = msg_box.button(QMessageBox.No)
            no_button.setText("Seleccionar")
            cancel_button = msg_box.button(QMessageBox.Cancel)
            cancel_button.setText("Cancelar")
            # Mostrar el cuadro de diálogo
            choice = msg_box.exec()
            if choice == QMessageBox.Yes:
                self.create_db()
            elif choice == QMessageBox.No:
                self.select_db()
            return False
        # La base de datos ya existe
        return True


    def clean_data(self):
        ''''Limpia los datos de los cuadros de dialogo '''
        self.ui_ventana_principal.in_nombre.clear()
        self.ui_ventana_principal.in_edad.clear()
        self.ui_ventana_principal.in_oi.clear()
        self.ui_ventana_principal.in_od.clear()
        self.ui_ventana_principal.in_adede.clear()
        self.ui_ventana_principal.in_observaciones.clear()
        self.ui_ventana_principal.in_fecha.setDate(QDate.currentDate())


    def add_client(self):
        '''Función usada para agrear un cliente'''
        # Llamar a la función para mostrar el diálogo y verificar la base de datos
        if not self.show_db_dialog():
            # No se ha seleccionado ni creado una base de datos.
            return
        # Obtener los valores de los QLineEdit y el QDateEdit
        nombre = self.ui_ventana_principal.in_nombre.text()
        edad = self.ui_ventana_principal.in_edad.text()
        oi = self.ui_ventana_principal.in_oi.text()
        od = self.ui_ventana_principal.in_od.text()
        adede = self.ui_ventana_principal.in_adede.text()
        observaciones = self.ui_ventana_principal.in_observaciones.text()
        fecha = self.ui_ventana_principal.in_fecha.date().toString("dd/MM/yyyy")
        if not nombre:
            QMessageBox.information(self, "Advertencia", "Escriba el nombre del cliente para agregarlo.")
            return
        edad = edad.replace(",", "")
        if nombre and edad.isdigit():
        # edad.isdigit() tiene como funcion verificar si "edad" es una cadena que contenga unicamente digitos numericos
            edad = int(edad)
        if edad and int(edad) < 0:
            QMessageBox.information(self, "Advertencia", "La edad no puede ser un número negativo.")
            return
        try:
            # Crear una lista con los datos del cliente
            cliente = (nombre, edad, oi, od, adede, observaciones, fecha)
            add_client_connection(cliente, self.db.databaseName())
            self.model.select()
            self.clean_data()
            # Mostrar un mensaje de información después de agregar el cliente
            QMessageBox.information(self, "Éxito al agregar", f"El cliente '<b>{nombre}</b>' ha sido agregado con éxito.")
        except RuntimeError as e:
            QMessageBox.warning(self, "Error al agregar cliente", str(e))
        except Exception as ex:
            QMessageBox.warning(self, "Error fatal al agregar cliente", f"Ocurrió un error inesperado al intentar agregar un cliente.\n\nError: '{type(ex).__name__}:  {str(ex)}'")


    def edit_client(self):
        '''Función usada para editar un cliente'''
        if not self.db.databaseName():
            QMessageBox.warning(self, "Advertencia", "Seleccione una base de datos antes de editar un cliente.")
            return
        # Obtener los índices de las filas seleccionadas en la tabla
        selected_indexes = self.ui_ventana_principal.tableView.selectionModel().selectedIndexes()
        if len(selected_indexes) == 0:
            # Mostrar un mensaje si no hay filas seleccionadas
            QMessageBox.information(self, "Advertencia", "Por favor, seleccione un cliente en la tabla para editarlo.")
            return
        # Obtener los índices de las filas seleccionadas; set() se encarga que no se repita ninguna fila
        unique_selected_rows = set(index.row() for index in selected_indexes)  
        # Obtener el número de clientes seleccionados
        num_selected_client = len(unique_selected_rows)
        if num_selected_client > 1:
            # Mostrar un mensaje si se han seleccionado múltiples cliente
            QMessageBox.information(self, "Advertencia", "Solo se puede editar un cliente a la vez.")
            return
        # Obtener los índices de las columnas seleccionadas
        unique_selected_columns = set(item.column() for item in selected_indexes)
        # Verificar si todas las columnas seleccionadas pertenecen al mismo cliente
        if len(unique_selected_columns) > 0:
            selected_row = list(unique_selected_rows)[0]
            client_id = self.model.index(selected_row, 0).data()
            for index in selected_indexes:
                row = index.row()
                if self.model.index(row, 0).data() != client_id:
                    # Mostrar un mensaje si las columnas seleccionadas pertenecen a diferentes usuarios
                    QMessageBox.information(self, "Advertencia", "Solo se puede editar un cliente a la vez.")
                    return
        # Obtener los datos del clientes seleccionado
        id_cliente = self.model.index(selected_row, 0).data()
        nombre = self.model.index(selected_row, 1).data()
        edad = self.model.index(selected_row, 2).data()
        oi = self.model.index(selected_row, 3).data()
        od = self.model.index(selected_row, 4).data()
        adede = self.model.index(selected_row, 5).data()
        observaciones = self.model.index(selected_row, 6).data()
        fecha = self.model.index(selected_row, 7).data()
        # Crear una instancia del diálogo de edición y pasar la instancia de MainWindow
        dialog = EditDialog(self, nombre, edad, oi, od, adede, observaciones, fecha, id_cliente, self.db.databaseName())
        if dialog.exec_() == QDialog.Accepted:
            # Actualizar el modelo de la tabla para reflejar los cambios
            self.model.select()
            QMessageBox.information(self, "Guardado exitoso", "Cambios guardados con exito.")


    def delete_client(self):
        '''Función usada para eliminar un cliente'''
        if not self.db.databaseName():
            QMessageBox.warning(self, "Advertencia", "Seleccione una base de datos antes de eliminar un cliente.")
            return
        selected_indexes = self.ui_ventana_principal.tableView.selectionModel().selectedIndexes()
        if len(selected_indexes) == 0:
            QMessageBox.information(self, "Advertencia", "Por favor, selecciona uno o más clientes de la tabla para eliminarlos.")
            return
        unique_selected_rows = set(index.row() for index in selected_indexes)
        num_selected_clients = len(unique_selected_rows)
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Eliminar cliente(s)")
        if num_selected_clients == 1:
            # Si solo se seleccionó un cliente, mostrar el nombre del cliente a eliminar
            client_name = self.model.index(list(unique_selected_rows)[0], 1).data()
            msg_box.setText(f"¿Estás seguro de que deseas eliminar al cliente: '<b>{client_name}</b>'?")
        else:
            # Crear una lista de nombres de los clientes seleccionados en caso de haber seleccionado más de un cliente
            selected_client_name = [self.model.index(row, 1).data() for row in unique_selected_rows]
            # Si se seleccionaron varios clientes, mostrar el número y nombre de los clientes seleccionados
            list_names = "'\n'".join(selected_client_name)
            msg_box.setText(f"Se eliminaran los siguientes {num_selected_clients} clientes:\n\n'{list_names}' \n\n¿Desear continuar?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        yes_button = msg_box.button(QMessageBox.Yes)
        yes_button.setText("Sí")
        choice = msg_box.exec()
        if choice == QMessageBox.Yes:
            try:
                # Eliminar los clientes de la base de datos
                ids_clients = [self.model.index(row, 0).data() for row in unique_selected_rows]
                name_clients = [self.model.index(row, 1).data() for row in unique_selected_rows]
                delete_client_connection(ids_clients, self.db.databaseName())
                self.model.select()
                # Actualizar el modelo de la tabla para reflejar los cambios
                QMessageBox.information(self, "Cliente(s) eliminado(s)", f"Cliente(s): <b>{name_clients}</b> eliminado(s) exitosamente.")
            except RuntimeError as e:
                QMessageBox.warning(self, "Error al eliminar cliente", str(e))
            except Exception as ex:
                QMessageBox.warning(self, "Error fatal al eliminar cliente", f"Ocurrió un error inesperado al intentar eliminar un cliente.\n\nError: '{type(ex).__name__}:  {str(ex)}'")



    def search_name(self):
        '''Función usada para buscar el nombre de un cliente'''
        # Obtener el valor de búsqueda del nombre
        search_name = self.ui_ventana_principal.in_buscar_nombre.text()
        if not search_name:
            QMessageBox.information(self, "Advertencia", "Por favor, escriba un nombre para buscarlo.")
            return
        # Actualizar el modelo de la tabla con los resultados encontrados
        self.model.setFilter("nombre LIKE '%{}%'".format(search_name))
        self.model.select()
        # Limpiar el QLineEdit in_buscar_nombre
        self.ui_ventana_principal.in_buscar_nombre.clear()


    def search_date(self):
        '''Función usada para buscar la fecha de registro de un cliente'''
        search_date_qdate = self.ui_ventana_principal.in_buscar_fecha.date()
        # Convertir el QDateEdit a formato de cadena "dd/mm/yyyy"
        search_date_str = search_date_qdate.toString("dd/MM/yyyy")
        self.model.setFilter("fecha = '{}'".format(search_date_str))
        self.model.select()


    def reset_table(self):
        """Function usada para volver a cargar la tabla."""
        # Cerrar el modelo
        self.model.clear()
        # Volver a abrir el modelo
        self.setup_model()
        # Volver a configurar la tabla
        self.setup_table()


    def sort_box(self):
        '''Ordena la tabla por columna seleccionada en el QComboBox'''
        # Obtener el índice de columna correspondiente a la opción seleccionada
        current_text = self.ui_ventana_principal.ordenar_tabla.currentText()
        if current_text == "Nombre":
            column_index = 1
        elif current_text == "Añadido":
            column_index = 0
        elif current_text == "Fecha":
            column_index = 7
        else:
            column_index = 0  # Por defecto, si la opción no coincide, usar la columna 0
        if self.current_order == Qt.AscendingOrder:
            new_order = Qt.DescendingOrder
        else:
            new_order = Qt.AscendingOrder
        self.model.setSort(column_index, new_order)
        self.model.select()
        self.ui_ventana_principal.tableView.setModel(self.model)
        self.current_order = new_order
        return column_index


    def toggle_order(self):
        '''Alterna entre orden ascendente y descendente al hacer clic en el botón de alternancia'''
        if not self.sort_box():
            return
        current_column = self.sort_box()
        # Verifica si current_column existe en el objeto self
        self.current_order = Qt.DescendingOrder if self.current_order == Qt.AscendingOrder else Qt.AscendingOrder
        self.model.setSort(current_column, self.current_order)
        self.model.select()
        self.ui_ventana_principal.tableView.setModel(self.model)


    def hide_menu (self):
        '''Usado para ocultar el widget lateral'''
        is_hidden = not self.ui_ventana_principal.widget_izquierda.isHidden()
        self.ui_ventana_principal.widget_izquierda.setHidden(is_hidden)



# Clase para el diálogo de edición
class EditDialog(QDialog):
    '''Clase del dialogo mostrado al ediitar un cliente'''
    def __init__(self, main_window, nombre, edad, oi, od, adede, observaciones, fecha, id_cliente, database_name):
        super().__init__()
        # Configurar las banderas de la ventana para eliminar el botón de ayuda "?"
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        # Guardar las instancias de MainWindow
        self.main_window = main_window
        self.id_cliente = id_cliente
        self.database_name = database_name

        # Instancia de la clase generada en VentanaPrincipal.py
        self.ui_ventana_edicion = Ui_Dialog()
        self.ui_ventana_edicion.setupUi(self)

        # Cargar la interfaz de usuario desde el archivo .ui
        #loadUi("VentanaEdicion.ui", self)

        int_validator = QIntValidator()
        self.ui_ventana_edicion.in_edad_edit.setValidator(int_validator)

        # Configurar los valores iniciales en los QLineEdit y el QPlainTextEdit
        self.ui_ventana_edicion.in_nombre_edit.setText(nombre)
        self.ui_ventana_edicion.in_edad_edit.setText(str(edad))
        self.ui_ventana_edicion.in_oi_edit.setText(oi)
        self.ui_ventana_edicion.in_od_edit.setText(od)
        self.ui_ventana_edicion.in_adede_edit.setText(adede)
        self.ui_ventana_edicion.in_observaciones_edit.setText(observaciones)
        self.ui_ventana_edicion.in_fecha_edit.setDate(QDate.fromString(fecha, "dd/MM/yyyy"))
        # Conectar el botón "btn_guardar_datos" a la función guardar_datos
        self.ui_ventana_edicion.btn_guardar_datos.clicked.connect(self.edit_data)
        # Conectar el botón "btn_cancelar_datos" a la función reject usada para cerrar el QDialog
        self.ui_ventana_edicion.btn_cancelar_datos.clicked.connect(self.reject)


    def edit_data(self):
        '''Guardar los cambos realizados al editar un cliente'''
        # Obtener los valores de los QLineEdit y el QDateEdit
        nombre = self.ui_ventana_edicion.in_nombre_edit.text()
        edad = self.ui_ventana_edicion.in_edad_edit.text()
        oi = self.ui_ventana_edicion.in_oi_edit.text()
        od = self.ui_ventana_edicion.in_od_edit.text()
        adede = self.ui_ventana_edicion.in_adede_edit.text()
        observaciones = self.ui_ventana_edicion.in_observaciones_edit.text()
        fecha = self.ui_ventana_edicion.in_fecha_edit.date().toString("dd/MM/yyyy")
        if not nombre:
            QMessageBox.information(self, "Advertencia", "El nombre es obligatorio.")
            return
        edad = edad.replace(",", "")
        if nombre and edad.isdigit():
            edad = int(edad)
        if edad and int(edad) < 0:
            QMessageBox.information(self, "Advertencia", "La edad no puede ser un número negativo.")
            return
        try:
            updated_client = (nombre, edad, oi, od, adede, observaciones, fecha, self.id_cliente)
            edit_client_connection(updated_client, self.database_name)
        except RuntimeError as e:
            QMessageBox.warning(self, "Error al editar usuario", str(e))
        except Exception as ex:
            QMessageBox.warning(self, "Error inesperado al editar usuario", f"Ocurrió un error inesperado al intentar editar el cliente: '<b>{nombre}</b>'.\n\nError: '{type(ex).__name__}:  {str(ex)}'")
        # Cerrar el diálogo de edición
        self.accept()



# Código para iniciar la aplicación y mostrar la ventana principal
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("images/icons/sunglasses.ico"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
