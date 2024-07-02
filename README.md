# CRUD-python-optica
Programa CRUD con creado con las siguientes tecnologias:
-Python (Versión: 3.12.1) usando la libreria PyQt5 (Versión: 5.15.10)
-SQLite3 (Versión: 3.41.2)
-Conda (Versión: 23.11.0)
-git (Version 2.43.0.windows.1)

Enfocado en solucionar las administración e información de los clientes en una optica, con la capacidad de 
-Crear clientes y guardarlos en una tabla interactiva, capacidad de editarlos desde la tabla o desde una ventana externa y eliminar los clientes.
-Capacidad para crear, copiar, seleccionar y eliminar la base de datos.
-Buscar clientes por nombre o fecha de registro.

![Ventana principal del programa](preview.png)

## Función de los archivos:
main.py: se encarga de la lógica del programa (Ejecutar este codigo para iniciar el programa).
conexion.py: Encargado de las consultas realizadas a la base de datos SQLite.
VentanaPrincipal.py: Es la interfaz grafica principal.
VentanaEdicion.py: Dialogo que aparece al editar un cliente.
imagenes_ui.py: Usado para configurar las los iconos de botones.
Carpeta images: Es donde se alojan las imagenes.