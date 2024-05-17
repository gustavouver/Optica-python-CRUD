'''Archivo creado por gustavo'''
import os
import sqlite3

FOLDER_DB = "Base_de_datos"
TABLA_CLIENTES = "clientes"

def create_db_connection(database_path=None):
    '''Conecta a la base de datos mediante sqlite3, crea la tabla clientes y sus atibutos'''
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS {TABLA_CLIENTES} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT,
                        edad INTEGER,
                        oi TEXT,
                        od TEXT,
                        adede TEXT,   
                        observaciones TEXT,
                        fecha DATE
                        )''')
    except sqlite3.Error as e:
        raise RuntimeError(f"Error: {e}.\n_Ocurrió un error al intentar crear la tabla '{TABLA_CLIENTES}' de la base de datos: '<b>{database_path}</b>'")
    finally:
        if conn:
            conn.close()

def delete_db_connection(database_path):
    '''Esta función elimina la base de datos proporcionada por el usuario'''
    # Cierra cualquier conexión activa a la base de datos si la hay
    try:
        conn = sqlite3.connect(database_path)
        conn.close()
        # Elimina el archivo de la base de datos si existe
        if os.path.exists(database_path):
            os.remove(database_path)
    except sqlite3.Error as e:
        raise RuntimeError(f"Error: '{e}'.\nOcurrió un error al intentar eliminar la base de datos '{database_path}'.")

def run_query(consulta, parametros=None, database_path=None):
    '''Ejecuta una consulta en la base de datos.'''
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        if parametros:
            cursor.execute(consulta, parametros)
        else:
            cursor.execute(consulta)
        conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(e)
    finally:
        if conn:
            conn.close()

def add_client_connection(cliente, database_path=None):
    '''Añade un cliente a la base de datos.'''
    run_query(f'''INSERT INTO {TABLA_CLIENTES} (
                            nombre, edad, oi, od, adede, observaciones, fecha
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)''', cliente, database_path)

def edit_client_connection(cliente, database_path=None):
    '''Edita un cliente de la base de datos.'''
    run_query(f'''UPDATE {TABLA_CLIENTES} SET
                            nombre=?, edad=?, oi=?, od=?, adede=?, observaciones=?, fecha=?
                            WHERE id=?''', cliente, database_path)

def delete_client_connection(id_client, database_path=None):
    '''Elimina un cliente de la base de datos.'''
    for each_client in id_client:
        run_query(f"DELETE FROM {TABLA_CLIENTES} WHERE id=?", (each_client,), database_path)
