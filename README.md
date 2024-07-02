# CRUD-python-optica
Programa CRUD con creado con las siguientes tecnologias:<br>
-Python (Versión: 3.12.1) usando la libreria PyQt5 (Versión: 5.15.10)<br>
-SQLite3 (Versión: 3.41.2)<br>
-Conda (Versión: 23.11.0)<br>
-git (Version 2.43.0.windows.1)<br>

Enfocado en solucionar las administración e información de los clientes en una optica, con la capacidad de:<br>
-Crear clientes y guardarlos en una tabla interactiva, capacidad de editarlos desde la tabla o desde una ventana externa y eliminar los clientes.<br>
-Capacidad para crear, copiar, seleccionar y eliminar la base de datos.<br>
-Buscar clientes por nombre o fecha de registro.<br>

![Ventana principal del programa](preview.png)<br>

## Función de los archivos:<br>
main.py: se encarga de la lógica del programa (Ejecutar este codigo para iniciar el programa).<br>
conexion.py: Encargado de las consultas realizadas a la base de datos SQLite.<br>
VentanaPrincipal.py: Es la interfaz grafica principal.<br>
VentanaEdicion.py: Dialogo que aparece al editar un cliente.<br>
imagenes_ui.py: Usado para configurar las los iconos de botones.<br>
Carpeta images: Es donde se alojan las imagenes.<br>
