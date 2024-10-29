'''
Codigo creado por: Gustavo López P.
'''
import sqlite3

TABLA_CLIENTES = "clientes"

def create_db_connection(database_path=None):
    '''Conecta a la base de datos (o la crea en caso de no existir) 
    mediante sqlite3 y crea la tabla clientes'''
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
        conn.commit() # Guarda los cambios
    except (sqlite3.OperationalError, sqlite3.IntegrityError, sqlite3.Error) as e:
        raise RuntimeError(f"Error operativo al hacer la consulta: {e}") from e
    finally:
        if conn:
            conn.close()


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
    except (sqlite3.OperationalError, sqlite3.IntegrityError, sqlite3.Error) as e:
        raise RuntimeError(f"Error operativo al hacer la consulta: {e}") from e
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
