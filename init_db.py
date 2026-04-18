import sqlite3
import os

# --- CONFIGURACIÓN DE RUTAS ---
DB_PATH = 'ctf_database.db'
FLAG_DIR = 'flags'  # Carpeta donde esconderemos el flag de Traversal
DOCS_DIR = 'docs'   # Carpeta pública de documentos

def setup_files():
    # Creamos los directorios si no existen para evitar errores de lectura
    os.makedirs(FLAG_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    # FLAG 1 (Reto de Directory Traversal)
    # Lo ponemos en una carpeta secreta. El estudiante debe 'escapar' de /docs/ para llegar aquí.
    with open(os.path.join(FLAG_DIR, 'flag1.txt'), 'w') as f:
        f.write('CTF{traversal_completo_2026}')
    
    # Archivo legítimo para que el estudiante tenga algo que ver al principio
    with open(os.path.join(DOCS_DIR, 'nota.txt'), 'w') as f:
        f.write('Bienvenido al explorador corporativo. No intentes ver archivos fuera de esta carpeta.')

def setup_db():
    # Si ya existe una base de datos antigua, la borramos para empezar de cero (limpieza)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # --- CREACIÓN DE TABLAS ---
    # Tabla de usuarios normales para el buscador
    cursor.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, role TEXT)')
    
    # Tabla secreta donde esconderemos el segundo flag (SQL Injection)
    cursor.execute('CREATE TABLE identidad (id INTEGER PRIMARY KEY, name TEXT, value TEXT)')
    
    # --- SIEMBRA DE DATOS (SEEDING) ---
    cursor.execute("INSERT INTO users (username, role) VALUES ('admin', 'Administrador Global')")
    cursor.execute("INSERT INTO users (username, role) VALUES ('carlos', 'Auditor Senior')")
    cursor.execute("INSERT INTO users (username, role) VALUES ('invitado', 'Usuario de Lectura')")
    
    # Insertamos el FLAG de SQLi en la tabla 'identidad'
    cursor.execute("INSERT INTO identidad (name, value) VALUES ('FLAG_SQLI', 'CTF{sqli_completo_2026}')")
    
    conn.commit()
    conn.close()
    print("✅ Infraestructura y Base de Datos inicializadas correctamente.")

if __name__ == '__main__':
    setup_files()
    setup_db()
