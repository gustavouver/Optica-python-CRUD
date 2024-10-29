'''
Codigo creado por: Gustavo López P.
Usando las tecnologías:
    -Python (Versión: 3.12.1)
    -PyQt5 (Versión: 5.15.10)
    -SQLite3 (Versión: 3.41.2)
    -Conda (Versión: 23.11.0)
    -git (Version 2.43.0.windows.1)
    -ChatGPT
'''
import os
import sys
import json
import shutil
# pylint: disable=no-name-in-module (Linea añadida para eviatar un falso error dado por pylint en la importacion de modulos)
from PyQt5.QtCore import QDate, Qt, QPropertyAnimation, QSequentialAnimationGroup, QPauseAnimation
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDialog, QMessageBox,
                            QAbstractItemView, QFileDialog, QHeaderView, QGraphicsOpacityEffect)
from VentanaPrincipal import Ui_MainWindow
from VentanaEdicion import Ui_Dialog
from conexion import (create_db_connection, add_client_connection,
                    edit_client_connection, delete_client_connection)

class MainWindow(QMainWindow):
    """
    Esta clase extiende la funcionalidad de QMainWindow de PyQt5 
    para proporcionar una interfaz de usuario principal.
    """
    def __init__(self):
        """
        Constructor de la clase MainWindow encargada de realizar las configuraciones iniciales.
        """
        super().__init__() #  llama al constructor de la clase base QMainWindow

        # Es la clase principal de VentanaPrincipal.py y contiene la interfaz gráfica.
        self.ui = Ui_MainWindow()
        # Establece la interfaz gráfica en la ventana
        self.ui.setupUi(self)
        # Establece el titulo de la ventana
        self.setWindowTitle("Óptica León")

        # Inicializa valores predeterminados de las instancias
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.state = True
        self.model = QSqlTableModel() # Al crear esta instancia se abre una conexión no requerida
        self.db.close() # Cierra la conexion no requerida abierta anteriormente
        self.effect = QGraphicsOpacityEffect()
        self.animation_group = QSequentialAnimationGroup()
        self.current_order = Qt.DescendingOrder # Variable con el orden actual de la tabla

        # Configura la ruta según el entorno
        if getattr(sys, 'frozen', False):
            self.script_directory = os.path.dirname(sys.executable) # Ruta del .exe
        else:
            self.script_directory = os.path.dirname(os.path.abspath(__file__)) # Ruta de este codigo
        # Rutas absolutas para guardar archvios JSON y las bases de datos
        self.json_folder_path = os.path.join(self.script_directory, "json_folder")
        self.json_file_path = os.path.join(self.json_folder_path, "config.json")
        self.db_folder_path = os.path.join(self.script_directory, "BasesDeDatos")

        # Carga las primeras funciones vitales para el programa
        self.setup_actions()
        self.setup_database()
        if not self.db.isOpen():
            self.btns_state(False)
            return
        self.setup_model()
        self.setup_table()


    def setup_actions(self):
        ''' Conectar los botones y cuadros de dialogos con sus respectivas funciones'''
        # Acciones base de datos
        self.ui.btn_create_DB.clicked.connect(self.create_db)
        self.ui.btn_select_DB.clicked.connect(self.select_db)
        self.ui.btn_copy_DB.clicked.connect(self.copy_db)
        self.ui.btn_delete_DB.clicked.connect(self.delete_db)
        # Acciones cliente
        self.ui.btn_add_client.clicked.connect(self.add_client)
        self.ui.in_nombre.returnPressed.connect(self.add_client)
        self.ui.in_observaciones.returnPressed.connect(self.add_client)
        self.ui.btn_edit_client.clicked.connect(self.edit_client)
        self.ui.btn_delete_client.clicked.connect(self.delete_client)
        self.ui.btn_clear.clicked.connect(self.clear_boxes)
        # Acciones de busqueda
        self.ui.btn_search_name.clicked.connect(lambda: self.search("name"))
        self.ui.in_search_name.returnPressed.connect(lambda: self.search("name"))
        self.ui.btn_search_date.clicked.connect(lambda: self.search("date"))
        # Acciones de la tabla
        self.ui.btn_reset_table.clicked.connect(self.reset_table)
        self.ui.comboBox_order.currentIndexChanged.connect(lambda: self.sort_box("order"))
        self.ui.btn_toggle.clicked.connect(lambda: self.sort_box("toggle"))
        self.ui.tableView.horizontalHeader().sectionClicked.connect(lambda index: self.sort_box("table", column_number=index))
        # Ocultar el menu
        self.ui.btn_menu.clicked.connect(self.hide_menu)
        # Configurar fecha para iniciar en la fecha actual
        self.ui.in_fecha.setDate(QDate.currentDate())
        self.ui.in_search_date.setDate(QDate.currentDate())
        # Configura un rango de enteros para el campo de edad
        self.ui.in_edad.setValidator(QIntValidator(0, 999))


    def btns_state(self, state):
        '''Establecer el estado de los botones (activo/inactivo)'''
        self.state = state
        self.ui.form_client.setEnabled(state)

        self.ui.frame_busqueda.setEnabled(state)

        self.ui.frame_table_header.setEnabled(state)

        self.ui.btn_copy_DB.setEnabled(state)
        self.ui.btn_delete_DB.setEnabled(state)


    def setup_database(self):
        ''' Configurar la conexión a la base de datos'''
        if not os.path.exists(self.json_file_path): # Verifica si la ruta en "json_file_path" existe
            self.ui.lbl_db_path.setText('<span style="color: red;"><b>Crea o selecciona una base de datos para continuar.</b></span>')
            return
        try:
            # Intenta abrir el archivo "json_file_path" en modo lectura ("r" de read)
            with open(self.json_file_path, "r", encoding="utf-8") as json_read:
                json_file = json.load(json_read)
        except json.decoder.JSONDecodeError:
            # Manejar la excepción cuando el archivo JSON existe pero su lectura es invalida
            self.ui.lbl_db_path.setText("El archivo JSON está vacío o corrompido.")
            return
        # Verificar si el JSON tiene la clave "last_selected_db"
        if not "last_selected_db" in json_file:
            self.ui.lbl_db_path.setText("El archivo JSON no contiene la palabra clave 'last_selected_db'.")
            return
        last_selected_db = json_file["last_selected_db"] # Se guarda la ruta actual de la base de datos en el archivo JSON
        # Comprueba que la base de datos especificada en el archivo JSON exista y sea una base de datos valida
        if not last_selected_db or not os.path.exists(last_selected_db) or not last_selected_db.endswith(".db"):
            self.ui.lbl_db_path.setText("Error al cargar la base de datos, verifica que la ruta y la base de datos sea valida.<br> <b>Ruta actual:</b><br>" + last_selected_db)
            return
        # Se establece la conexión con la base de datos
        self.db.setDatabaseName(last_selected_db) # Establece el nombre de la base de datos
        self.db.open() # Abre la conexion de la base de datos
        # Se establecen las etiquetas de la base de datos y la tabla
        self.ui.lbl_db_path.setText(os.path.basename(self.db.databaseName()).replace(".db", ""))
        self.ui.lbl_table_order.setText("<b>Orden de la tabla:  </b>Añadido (\u2193)")
        self.ui.lbl_table_filter.setText(" ")


    def setup_model(self):
        '''Establece el modelo'''
        # Selecciona la tabla a usar
        self.model.setTable("clientes")
        # Establece  en el modelo la columna 0 (id) como orden descendente
        self.model.setSort(0, Qt.DescendingOrder)
        self.current_order = Qt.DescendingOrder
        # Establece la etiqueta del filtro en Añadido (id)
        self.ui.comboBox_order.setCurrentText("Añadido")
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
        # Establece la configuracion del modelo dentro de la tabla (llamada 'tableView')
        self.ui.tableView.setModel(self.model)
        # Asegura que la tabla esté al frente de otros elementos
        self.ui.tableView.raise_()
        # Establece el modo de selección de la tabla para permitir seleccion de multiples filas y columnas
        self.ui.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # Para las demás columnas, define un ajuste de contenido
        for col in range(1, 7):
            self.ui.tableView.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        # Ocultar la columna 0 (columna del id)
        self.ui.tableView.setColumnHidden(0, True)


    def switch_to_new_db(self, new_db, message="Conectar"):
        '''Hace las configuraciones necesarias para conectar a una nueva base de datos'''
        try:
            # Crear el folder JSON si no existe
            if not os.path.exists(self.json_folder_path):
                os.makedirs(self.json_folder_path)

            # Guardar el último nombre de la base de datos en el archivo JSON
            with open(self.json_file_path, "w", encoding="utf-8") as json_write:
                json_config = {"last_selected_db": new_db}
                json.dump(json_config, json_write) # json.dump(que, donde)

            # Operaciones críticas que podrían fallar
            self.db.close()
            self.setup_database()
            self.setup_model()
            self.setup_table()
            if not self.db.isOpen():
                raise RuntimeError(f"Error al intentar abrir la base de datos: {new_db}")
            return True

        except (AttributeError, TypeError, FileNotFoundError, PermissionError, OSError, RuntimeError) as ex:
            # Manejo de excepciones
            QMessageBox.warning(self, f"Error al {message} la base de datos",
                                f"Ocurrió un error al {message} la base de datos.\n\nError: '{type(ex).__name__} - {ex}'")
            return False


    def create_db(self):
        '''Establece la conexion, modelo, tabla y etiqueta de la nueva base de datos'''
        actual_db_dir = os.path.dirname(self.db.databaseName())
        # comprueba en que carpeta se encuentra la base de datos actual
        if actual_db_dir:
            destination_folder = actual_db_dir
        else:
            destination_folder = self.db_folder_path
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)  # Crear solo si no existe
        options = QFileDialog.Options()
        # 'new_db_name' es la ruta del archivo seleccionado por el usuario.
        # '_' es una variable que recibe el filtro de archivos seleccionados
        new_db_name, _ = QFileDialog.getSaveFileName(self,
                                                    "Guardar Nueva Base de Datos", # Nombre de la ventana
                                                    destination_folder, # Ruta donde se abrirá la ventana
                                                    "SQLite Database Files (*.db);;All Files (*)", # Filtros para guardar el archivo
                                                    options=options)
        if not new_db_name:
            return
        # Asegurarse de que la extensión '.db' esté presente al final de la base de datos
        if not new_db_name.lower().endswith(".db"):
            # Se agrega al final la extensión ".db" en caso de no existir
            new_db_name += ".db"
        try:
            # Llamar a la función dentro del archivo conexion.py para crear la nueva base de datos 
            create_db_connection(new_db_name)
        except RuntimeError as e:
            QMessageBox.warning(self, "Error al crear base de datos", str(e))
            return
        if not self.switch_to_new_db(new_db_name, message="crear"):
            return
        self.btns_state(True)
        QMessageBox.information(self, "Éxito al crear",
                                f"La nueva base de datos fue creada con éxito.<br><br>Ahora trabajas con la base de datos: <b>{os.path.basename(self.db.databaseName()).replace(".db", "")}</b>")


    def select_db(self):
        '''Función usada para seleccionar una nueva base de datos'''
        options_config = QFileDialog.Options()
        # Operador "bitwise OR" indica que el cuadro de diálogo debe abrirse en modo de solo lectura
        options_config |= QFileDialog.ReadOnly
        actual_db_dir = os.path.dirname(self.db.databaseName())
        destination_folder = actual_db_dir if actual_db_dir else self.db_folder_path
        selected_db, _ = QFileDialog.getOpenFileName(self,
                                                    "Seleccionar base de datos",
                                                    destination_folder,
                                                    "Archivos de base de datos (*.db);;Todos los archivos (*)",
                                                    options=options_config)
        if not selected_db:
            return
        if not selected_db.endswith(".db"):
            QMessageBox.information(self, "Error al seleccionar",
                                    "Error al seleccionar, verifique que el archivo seleccionado sea una base de datos valida.")
            return
        if not self.switch_to_new_db(selected_db, message="seleccionar"):
            return
        self.btns_state(True)
        QMessageBox.information(self, "Éxito al seleccionar",
                                f"La nueva base de datos fue seleccionada con éxito.<br><br>Ahora trabajas con la base de datos: <b>{os.path.basename(self.db.databaseName()).replace(".db", "")}</b>")


    def show_confirmation_dialog(self, title="titulo_SCD", message="mensaje_SCD", yes_text="Sí", no_text="No"):
        '''Función general para mostrar un diálogo de confirmación'''
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        yes_button = msg_box.button(QMessageBox.Yes)
        yes_button.setText(yes_text)
        no_button = msg_box.button(QMessageBox.No)
        no_button.setText(no_text)
        choice = msg_box.exec()
        return choice == QMessageBox.Yes


    def copy_db(self):
        '''Función usada para copiar la base de datos actual'''
        if not self.db.isOpen() or not os.path.exists(self.db.databaseName()):
            QMessageBox.warning(self, "Error de conexión",
                                "No hay ninguna base de datos abierta para copiar.")
            return
        options_config = QFileDialog.Options()
        options_config |= QFileDialog.ReadOnly
        original_name = self.ui.lbl_db_path.text() # Obtiene el nombre actual de la base de datos
        copy_name = f"{original_name}-copia.db"
        actual_db_dir = os.path.dirname(self.db.databaseName())
        destination_folder = actual_db_dir if actual_db_dir else self.db_folder_path
        new_db, _ = QFileDialog.getSaveFileName(self,
                                                "Guardar copia de la base de datos",
                                                os.path.join(destination_folder, copy_name),
                                                "Archivos de base de datos (*.db);;Todos los archivos (*)",
                                                options=options_config)
        if not new_db:
            return
        # Verifica si el usuario está intentando guardar la copia con el mismo nombre que la base de datos original
        if os.path.abspath(new_db) == os.path.abspath(self.db.databaseName()):
            QMessageBox.warning(self, "Error al copiar", "No se puede reemplazar la base de datos original con una copia idéntica.")
            return
        try:
            # Realizar la copia de la base de datos en la nueva ubicación
            shutil.copy2(self.db.databaseName(), new_db) # shutil.copy2 copia tambien los metadatos
        except (FileNotFoundError, PermissionError, IsADirectoryError, OSError) as ex:
            QMessageBox.warning(self, "Error al copiar la base de datos", f"Ocurrió un error al copiar la base de datos.\n\nError: '{type(ex).__name__} - {ex}'")
            return
        new_db_name = os.path.basename(new_db).replace(".db", "")
        if not self.show_confirmation_dialog(title="Copia exitosa",
                                    message=f"Copia creada exitosamente.<br><br> ¿Deseas cambiar la conexion a la nueva copia creada <b>{new_db_name}</b> o seguir trabajando con la base de datos actual <b>{original_name}</b>?",
                                    yes_text="Nueva copia creada",
                                    no_text="Original"):
            QMessageBox.information(self, "Correcto", "Sigues trabajando con la base de datos original.")
            return
        self.switch_to_new_db(new_db, "seleccionar")
        QMessageBox.information(self, "Correcto", f"Ahora trabajas con la nueva copia creada: <b>{new_db_name}</b>.")


    def delete_db(self):
        '''Función usada para eliminar la base de datos actual'''
        if not self.db.isOpen() or not os.path.exists(self.db.databaseName()):
            QMessageBox.warning(self, "Advertencia", "No hay ninguna base de datos abierta para eliminar.")
            return
        current_db_path = self.db.databaseName()
        current_db_name = os.path.basename(current_db_path).replace(".db", "")

        if not self.show_confirmation_dialog(title="Eliminar base de datos",
                                    message=f"¿Estás seguro de eliminar la base de datos: '<b>{current_db_name}</b>'?", 
                                    yes_text="Sí",
                                    no_text="No"):
            return
        self.db.close()
        try:
            # Elimina el archivo de la base de datos si existe
            if os.path.exists(current_db_path):
                os.remove(current_db_path)
            if os.path.exists(self.json_file_path):
                os.remove(self.json_file_path) # Elimina el archivo JSON
        except (PermissionError, FileNotFoundError, OSError) as ex:
            QMessageBox.warning(self, 
                                "Error al eliminar", 
                                f"Ocurrió un error al tratar de eliminar la base de datos.\n\nError: '{type(ex).__name__} - {ex}'")
            return
        # Limpiar el modelo
        self.model.clear()
        self.btns_state(False)
        self.ui.lbl_db_path.setText('<span style="color: red;"><b>No existe conexión con ninguna base de datos<br>Crea o selecciona una base de datos para continuar.</b></span>')
        QMessageBox.information(self, "Eliminacion exitosa",
                                f"La base de datos <b>{current_db_name}</b> se eliminó correctamente.")


    def clear_boxes(self):
        ''''Limpia los datos de los cuadros de dialogo '''
        self.ui.in_nombre.clear()
        self.ui.in_edad.clear()
        self.ui.in_oi.clear()
        self.ui.in_od.clear()
        self.ui.in_adede.clear()
        self.ui.in_observaciones.clear()
        self.ui.in_fecha.setDate(QDate.currentDate())


    def add_client(self):
        '''Función usada para agrear un cliente'''
        # No se ha seleccionado ni creado una base de datos.
        if not self.db.isOpen() or not os.path.exists(self.db.databaseName()):
            QMessageBox.information(self, "No existe conexion con una base de datos",
                                    "Debes crear o seleccionar una base de datos para agregar un cliente")
            return
        # Obtener los valores de los QLineEdit y el QDateEdit
        nombre = self.ui.in_nombre.text()
        edad = self.ui.in_edad.text()
        oi = self.ui.in_oi.text()
        od = self.ui.in_od.text()
        adede = self.ui.in_adede.text()
        observaciones = self.ui.in_observaciones.text()
        fecha = self.ui.in_fecha.date().toString("dd/MM/yyyy")
        edad = edad.replace(",", "") # Elimina las comas en caso haberlas
        if not nombre: # Nombre obligatorio
            QMessageBox.information(self, "Advertencia", "Introduzca un nombre para agregar al cliente.")
            return
        if nombre and edad.isdigit(): # Verifica que el campo de edad sea un numero entero sin espacios
            edad = int(edad)
        if edad and int(edad) < 0: # Seguridad extra: La edad tiene un rango establecido en el init de 0 a 999
            QMessageBox.information(self, "Advertencia", "La edad no puede ser un número negativo.")
            return
        cliente = (nombre, edad, oi, od, adede, observaciones, fecha)
        try:
            # Crear una lista con los datos del cliente
            add_client_connection(cliente, self.db.databaseName())
        except RuntimeError as e:
            QMessageBox.warning(self, "Error al agregar cliente", str(e))
            return
        self.model.select()
        self.clear_boxes()
        QMessageBox.information(self, "Éxito al agregar",
                                f"El cliente '<b>{nombre}</b>' fue agregado con éxito.")


    def edit_client(self):
        '''Función usada para editar un cliente'''
        if not self.db.databaseName():
            QMessageBox.warning(self, "Advertencia", "Seleccione una base de datos antes de editar un cliente.")
            return
        # Obtener los índices de las filas seleccionadas en la tabla
        selected_indexes = self.ui.tableView.selectionModel().selectedIndexes()
        if not selected_indexes:
            QMessageBox.information(self, "Advertencia", "Selecciona un cliente en la tabla para editarlo.<br><br>También puedes editar los datos directamente en la tabla.")
            return
        # Obtener filas unicas, crea un conjunto de las filas donde no permite duplicados (set() es lo mismo que usar {})
        unique_selected_rows = {index.row() for index in selected_indexes} # {} crea un conjunto unico de las filas
        if len(unique_selected_rows) > 1: # Si se selecciona mas de una fila (cliente)
            QMessageBox.information(self, "Advertencia", "Solo se puede editar un cliente a la vez.<br><br>También puedes editar los datos directamente en la tabla.")
            return
        # Obtener la fila seleccionada (sabemos que hay solo una fila)
        selected_row = unique_selected_rows.pop()
        # Obtener los datos del clientes seleccionado
        id_cliente = self.model.index(selected_row, 0).data()
        nombre = self.model.index(selected_row, 1).data()
        edad = self.model.index(selected_row, 2).data()
        oi = self.model.index(selected_row, 3).data()
        od = self.model.index(selected_row, 4).data()
        adede = self.model.index(selected_row, 5).data()
        observaciones = self.model.index(selected_row, 6).data()
        fecha = self.model.index(selected_row, 7).data()
        client_data = (id_cliente, nombre, edad, oi, od, adede, observaciones, fecha)
        # Crear una instancia del diálogo de edición y pasar la instancia de MainWindow
        dialog = EditDialog(self, client_data, self.db.databaseName())
        try:
            if dialog.exec_() == QDialog.Accepted:
                # Actualizar el modelo de la tabla para reflejar los cambios
                self.model.select()
                QMessageBox.information(self, "Edición exitosa", f"Los cambios realizados en el cliente '<b>{dialog.updated_name}</b>' fueros realizados correctamente.")
        except RuntimeError as e:
            QMessageBox.warning(self, "Error al agregar cliente", str(e))
            return

    def delete_client(self):
        '''Función usada para eliminar un cliente'''
        if not self.db.databaseName():
            QMessageBox.warning(self, "Advertencia", "Seleccione una base de datos antes de eliminar un cliente.")
            return
        selected_indexes = self.ui.tableView.selectionModel().selectedIndexes()
        if not selected_indexes:
            QMessageBox.information(self, "Advertencia", "Selecciona uno o más clientes de la tabla para eliminarlos.")
            return
        
        unique_selected_rows = {index.row() for index in selected_indexes}
        selected_client_names = ", ".join(self.model.index(row, 1).data() for row in unique_selected_rows)
        num_selected_clients = len(unique_selected_rows)

        message_msg = (f"¿Estás seguro de que deseas eliminar al cliente: <b>{selected_client_names}</b>?"
                    if num_selected_clients == 1
                    else f"Se eliminarán los siguientes {num_selected_clients} clientes: <br><br><b>{selected_client_names}</b><br><br>¿Deseas continuar?")

        if self.show_confirmation_dialog(title="Eliminar cliente(s)",
                                        message=message_msg,
                                        yes_text="Eliminar",
                                        no_text="Cancelar"):
            try:
                ids_clients = [self.model.index(row, 0).data() for row in unique_selected_rows]
                delete_client_connection(ids_clients, self.db.databaseName())
                self.model.select()
                # Actualizar el modelo de la tabla para reflejar los cambios
                QMessageBox.information(self, "Cliente(s) eliminado(s)",
                                        f"Cliente(s): '<b>{selected_client_names}</b>' eliminado(s) correctamente.")
            except RuntimeError as e:
                QMessageBox.warning(self, "Error al eliminar cliente(s)", str(e))


    def reset_table(self):
        """Function usada para volver a cargar la tabla."""
        if not self.db.databaseName():
            return
        self.setup_model()  # Configurar el modelo
        self.setup_table()  # Configurar la tabla
        self.ui.lbl_table_order.setText("<b>Orden de la tabla:</b>  Añadido (\u2193)")
        # Volver a establecer el modelo
        self.ui.lbl_table_filter.setText("Tabla restablecida")
        self.effect = QGraphicsOpacityEffect()
        self.animation_group = QSequentialAnimationGroup()
        self.ui.lbl_table_filter.setGraphicsEffect(self.effect)
        # Animación para aumentar
        fade_in = QPropertyAnimation(self.effect, b"opacity")
        fade_in.setDuration(500) # 500 milesimas de segundo
        fade_in.setStartValue(0) # Opacidad inicial 
        fade_in.setEndValue(1)   # Opacidad final
        pause = QPauseAnimation(800)  # 800 milesimas de segundo de pausa
        # Animación para disminuir la opacidad de 1 a 0 en 500 milesimas de segundo
        fade_out = QPropertyAnimation(self.effect, b"opacity")
        fade_out.setDuration(500)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        # Crear un grupo secuencial de animaciones
        self.animation_group.addAnimation(fade_in)  # Primero subir la opacidad
        self.animation_group.addAnimation(pause)    # Después esperar 800 milesimas de segundo
        self.animation_group.addAnimation(fade_out) # Finalmente bajar la opacidad
        # Iniciar la animación
        self.animation_group.start()
        # Después de la animación, establecer el QLabel en blanco
        self.animation_group.finished.connect(lambda: self.ui.lbl_table_filter.setGraphicsEffect(None))
        self.animation_group.finished.connect(lambda: self.ui.lbl_table_filter.setText(""))


    def search(self, search_type):
        '''Función usada para buscar el nombre de un cliente'''
        if not self.db.databaseName():
            QMessageBox.warning(self, "Advertencia", "Seleccione una base de datos antes de buscar un cliente.")
            return
        
        if search_type == "name":
            # Obtener el valor de búsqueda del nombre
            search_name = self.ui.in_search_name.text()
            if not search_name:
                QMessageBox.information(self, "Advertencia", "Escriba un nombre para buscarlo.")
                return
            # Actualizar el modelo de la tabla con los resultados encontrados
            self.model.setFilter(f"nombre LIKE '%{search_name}%'")
            # Limpiar el QLineEdit y 
            self.ui.in_search_name.clear()
            self.ui.lbl_table_filter.setText(f"<b>Filtro de busqueda:</b> {search_name}") # Establece el orden de busqueda en la etiqueta

        elif search_type == "date":
            search_date_str = self.ui.in_search_date.date().toString("dd/MM/yyyy")
            self.model.setFilter(f"fecha = '{search_date_str}'")
            self.ui.lbl_table_filter.setText(f"<b>Filtro de busqueda: </b> {search_date_str}")
        else:
            QMessageBox.information(self, "Error", "Surgió un error inesperado al realizar la busqueda.")
        
        self.model.select()
        # Verificar si hay coincidencias
        if self.model.rowCount() == 0:
            # Si no hay coincidencias, mostrar un mensaje en el QTableView
            QMessageBox.information(self, "Sin coincidencias", f"No se encontraron coincidencias con la busqueda: '<b>{search_name if search_type == 'name' else search_date_str}<b/>'")
            self.reset_table()



    def sort_box(self, order_type, column_number=None):
        '''Ordena la tabla por columna seleccionada en el QComboBox'''
        if not self.db.databaseName():
            return
        # Mapeo de las opciones del ComboBox a los índices de las columnas
        column_mapping = {
            "Añadido": 0,
            "Nombre": 1,
            "Edad": 2,
            "OI": 3,
            "OD": 4,
            "ADD": 5,
            "Observs": 6,
            "Fecha": 7
        }
        # Obtener la opción seleccionada en el ComboBox
        order = self.ui.comboBox_order.currentText()
        # Obtener el índice de columna correspondiente a la opción seleccionada
        column_index = column_mapping.get(order, 0)  # Usa 0 como valor predeterminado
        # Verifica si el tipo de orden es "order" o "toggle"
        if order_type == "order":
            # Ordenar la tabla sin cambiar la dirección
            self.model.setSort(column_index, self.current_order)
        elif order_type == "toggle":
            # Alternar la dirección del orden
            self.current_order = Qt.DescendingOrder if self.current_order == Qt.AscendingOrder else Qt.AscendingOrder
            self.model.setSort(column_index, self.current_order)
        elif order_type == "table" and column_number is not None:
            # Alternar la dirección del orden cuando se selecciona desde el encabezado de la tabla
            self.current_order = Qt.DescendingOrder if self.current_order == Qt.AscendingOrder else Qt.AscendingOrder
            self.model.setSort(column_number, self.current_order)

        # Actualizar el modelo de la tabla
        self.model.select()
        # Actualizar la dirección para otros casos
        direction = " (\u2193)" if self.current_order == Qt.DescendingOrder else " (\u2191)"
        # Obtener el nombre de la columna para actualizar la etiqueta de orden
        column_name = next((k for k, v in column_mapping.items() if v == column_number), self.ui.comboBox_order.currentText())
        new_order = column_name if column_name else self.ui.comboBox_order.currentText()
        self.ui.lbl_table_order.setText("<b>Orden de la tabla:  </b>" + new_order + direction)


    def hide_menu(self):
        '''Usado para ocultar o mostrar el widget lateral y actualizar el botón'''
        # Verifica si el widget está oculto o visible
        hidden = not self.ui.left_widget.isHidden()
        # Cambia la visibilidad del widget
        self.ui.left_widget.setHidden(hidden)
        #el ícono del botón
        if hidden:
            self.ui.btn_menu.setIcon(QIcon(":/imagenes-monk/images/svg/hidden-eye.svg"))
        else:
            self.ui.btn_menu.setIcon(QIcon(":/imagenes-monk/images/svg/menu-icon.svg"))


# Clase para el diálogo de edición
class EditDialog(QDialog):
    '''Clase del dialogo mostrado al editar un cliente'''
    def __init__(self, main_window, client_data, database_path):
        super().__init__()
        # Es la clase principal de VentanaPrincipal.py y contiene la interfaz gráfica.
        self.ui_edit = Ui_Dialog()
        # Establece la interfaz gráfica como ventana principal
        self.ui_edit.setupUi(self)
        # Establece el titulo de la ventana
        self.setWindowTitle("Editar cliente")
        # Eliminar el botón de ayuda "?"
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        # Guardar las instancias de MainWindow
        self.main_window = main_window
        self.id_cliente = client_data[0]
        self.database_path = database_path
        self.updated_name = None
        # Establecer los valores iniciales en los campos del formulario
        self.set_initial_values(client_data)
        self.ui_edit.btn_guardar_datos.setDefault(True)
        # Conectar botones a sus funciones
        self.ui_edit.btn_guardar_datos.clicked.connect(self.edit_data)
        self.ui_edit.btn_cancelar_datos.clicked.connect(self.reject)


    def set_initial_values(self, client_data):
        '''Establecer los valores iniciales en los campos del formulario'''
        self.ui_edit.in_nombre_edit.setText(client_data[1])
        self.ui_edit.in_edad_edit.setText(str(client_data[2]))
        self.ui_edit.in_oi_edit.setText(client_data[3])
        self.ui_edit.in_od_edit.setText(client_data[4])
        self.ui_edit.in_adede_edit.setText(client_data[5])
        self.ui_edit.in_observaciones_edit.setText(client_data[6])
        self.ui_edit.in_fecha_edit.setDate(QDate.fromString(client_data[7], "dd/MM/yyyy"))
        # Validador de enteros para el campo edad (Acepta solo numeros del 0 al 999)
        self.ui_edit.in_edad_edit.setValidator(QIntValidator(0, 999))



    def edit_data(self):
        '''Guardar los cambos realizados al editar un cliente'''
        # Obtener los valores de los QLineEdit y el QDateEdit
        nombre = self.ui_edit.in_nombre_edit.text().strip()
        edad = self.ui_edit.in_edad_edit.text().replace(",", "").strip()
        oi = self.ui_edit.in_oi_edit.text().strip()
        od = self.ui_edit.in_od_edit.text().strip()
        adede = self.ui_edit.in_adede_edit.text().strip()
        observaciones = self.ui_edit.in_observaciones_edit.text().strip()
        fecha = self.ui_edit.in_fecha_edit.date().toString("dd/MM/yyyy")
        edad = edad.replace(",", "")
        if not nombre:
            QMessageBox.information(self, "Advertencia", "El nombre es obligatorio.")
            return
        if nombre and edad.isdigit():
            edad = int(edad)
        if edad and int(edad) < 0:
            QMessageBox.information(self, "Advertencia", "La edad no puede ser un número negativo.")
            return
        try:
            updated_client = (nombre, edad, oi, od, adede, observaciones, fecha, self.id_cliente)
            edit_client_connection(updated_client, self.database_path)
            self.updated_name = nombre  # Guarda el nombre actualizado
            self.accept()
        except RuntimeError as e:
            raise QMessageBox.warning(self, "Error al editar cliente", str(e)) from e


# Código para iniciar la aplicación
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/imagenes-monk/images/icons/sunglasses.ico"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
