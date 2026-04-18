import os
import sqlite3
import uuid
from flask import Flask, request, render_template_string, session, redirect, url_for

app = Flask(__name__)

# --- CONFIGURACIÓN E INICIALIZACIÓN ---

# Generamos una clave secreta aleatoria para que cada sesión de usuario sea única y segura
app.secret_key = str(uuid.uuid4()) 
DB_PATH = 'ctf_database.db'

# Función para conectar a la base de datos SQLite
# NOTA: En un entorno real usaríamos SQLAlchemy, pero para CTF el acceso crudo es más educativo
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    # Permite acceder a las columnas por nombre (ej: row['username'])
    conn.row_factory = sqlite3.Row
    return conn

# Definimos los retos como un diccionario para facilitar la gestión de niveles
LEVELS = {
    1: {
        "title": "Nivel 1: El Bypass",
        "category": "SQL Injection",
        "objective": "Logra que el sistema devuelva más de un usuario usando operadores lógicos.",
        "hint": "Prueba usar la lógica del 'OR' para que la condición siempre sea verdadera (ej: <code>' OR 1=1 --</code>).",
        "explanation": "Explotaste un Bypass de Autenticación. Al forzar la condición a Verdadero, anulaste el filtro del programador.",
        "prevention": "Usa consultas parametrizadas para evitar que el input del usuario sea parte del comando SQL."
    },
    2: {
        "title": "Nivel 2: Fuga de Información",
        "category": "SQL Injection",
        "objective": "Provoca un error en la base de datos que revele información técnica.",
        "hint": "Los caracteres especiales como la comilla simple <code>'</code> suelen romper la sintaxis si no están filtrados.",
        "explanation": "Inyección Basada en Errores. La aplicación muestra errores crudos del motor de búsqueda (SQLite), revelando detalles internos.",
        "prevention": "Desactiva la visualización de errores detallados en producción y usa manejadores de excepciones genéricos."
    },
    3: {
        "title": "Nivel 3: El Oráculo Ciego",
        "category": "SQL Injection",
        "objective": "Confirma la existencia del usuario 'admin' usando una condición lógica AND.",
        "hint": "Prueba inyectar una condición que sea verdadera: <code>admin' AND 1=1 --</code>. Luego prueba una falsa.",
        "explanation": "Inyección Booleana. Has aprendido a 'interrogar' a la base de datos mediante preguntas de Sí o No basándote en la respuesta de la página.",
        "prevention": "Valida que el input solo contenga caracteres permitidos y usa Prepared Statements."
    },
    4: {
        "title": "Nivel 4: El Gran Robo",
        "category": "SQL Injection",
        "objective": "Extrae el flag de la tabla oculta 'identidad'.",
        "hint": "Usa <code>UNION SELECT</code> para unir los resultados de la búsqueda con datos de la tabla <code>identidad (name, value)</code>.",
        "explanation": "Inyección UNION-Based. Has logrado extraer datos sensibles de tablas a las que no tenías acceso originalmente.",
        "prevention": "Principio de Menor Privilegio: La cuenta de la DB no debería poder leer tablas sensibles si no es necesario."
    },
    5: {
        "title": "Nivel 5: El Intruso de Archivos",
        "category": "Web / Directory Traversal",
        "objective": "Lee el archivo 'flag1.txt' ubicado en la carpeta '/flags/'.",
        "hint": "La aplicación busca en 'docs/'. Intenta 'subir' niveles usando <code>../</code> para salir de esa carpeta.",
        "explanation": "Directory Traversal. Has manipulado la ruta del archivo para acceder a áreas restringidas del servidor.",
        "prevention": "Sanea las rutas de archivos. Usa una lista blanca o funciones que limpien la ruta antes de abrir el archivo."
    }
}

# Estilos CSS Premium (Dashboard y Niveles)
BASE_STYLE = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700&display=swap');
    :root {
        --primary: #00ffcc; --secondary: #6e45e2; --bg: #0b0f19;
        --card: #161b22; --text: #f0f6fc; --accent: #f43f5e;
        --success: #238636; --locked: #30363d;
    }
    body { font-family: 'Outfit', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 0; }
    .nav { padding: 20px; background: rgba(0,0,0,0.5); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363d; }
    .container { max-width: 900px; margin: 40px auto; padding: 0 20px; text-align: center; }
    .level-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }
    .level-card { 
        background: var(--card); padding: 30px; border-radius: 20px; border: 1px solid #30363d;
        transition: transform 0.3s, border-color 0.3s; position: relative; overflow: hidden;
    }
    .level-card.unlocked:hover { transform: translateY(-5px); border-color: var(--primary); cursor: pointer; }
    .level-card.locked { opacity: 0.5; filter: grayscale(0.8); cursor: not-allowed; }
    .level-card.completed { border-color: var(--success); }
    .badge { position: absolute; top: 10px; right: 10px; padding: 5px 10px; border-radius: 8px; font-size: 0.7rem; font-weight: bold; }
    .btn { display: inline-block; padding: 12px 24px; border-radius: 12px; text-decoration: none; font-weight: bold; transition: 0.3s; border: none; cursor: pointer; }
    .btn-primary { background: var(--primary); color: #000; }
    .btn-abandon { background: transparent; border: 1px solid var(--accent); color: var(--accent); }
    .hint-box { margin-top: 20px; background: rgba(110,69,226,0.1); border: 1px dashed var(--secondary); border-radius: 12px; padding: 15px; text-align: left; }
    .success-panel { background: rgba(35,134,54,0.1); border: 2px solid var(--success); border-radius: 20px; padding: 30px; margin-top: 30px; animation: slideUp 0.5s; text-align: left;}
    @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { padding: 12px; border: 1px solid #30363d; text-align: left; }
    th { background: #161b22; }
</style>
'''

# --- RUTAS DE NAVEGACIÓN ---

# Inicializamos la sesión si es la primera vez que el estudiante entra
def init_session():
    if 'progress' not in session:
        session['progress'] = [] # Aquí guardamos los IDs de los niveles que vaya desbloqueando
    if 'total_attempts' not in session:
        session['total_attempts'] = 0

# Página Principal: Mapa de niveles
@app.route('/')
def dashboard():
    init_session()
    return render_template_string(BASE_STYLE + '''
        <div class="nav">
            <div style="font-weight: bold; font-size: 1.2rem;">🛡️ CTF Seg-APP 2026</div>
            <a href="/results" class="btn btn-abandon">Abandonar y Ver Resultados</a>
        </div>
        <div class="container">
            <h1>Mapa de Desafíos</h1>
            <p>Completa cada reto para desbloquear el siguiente nivel.</p>
            <div class="level-grid">
                {% for id, lv in levels.items() %}
                {% set is_unlocked = (id == 1 or (id-1) in progress) %}
                {% set is_completed = id in progress %}
                <div class="level-card {{ 'unlocked' if is_unlocked else 'locked' }} {{ 'completed' if is_completed else '' }}"
                     {% if is_unlocked %} onclick="window.location.href='/level/{{id}}'" {% endif %}>
                    
                    {% if is_completed %} <span class="badge" style="background: var(--success);">LOGRADO</span>
                    {% elif not is_unlocked %} <span class="badge" style="background: var(--locked);">BLOQUEADO</span>
                    {% else %} <span class="badge" style="background: var(--primary); color:#000;">DISPONIBLE</span>
                    {% endif %}

                    <h3>{{ lv.title }}</h3>
                    <p style="font-size: 0.9rem; opacity: 0.7;">{{ lv.category }}</p>
                </div>
                {% endfor %}
            </div>
            <div style="margin-top: 40px;">
                <button onclick="if(confirm('¿Borrar todo el progreso?')) window.location.href='/reset'" 
                        style="background:none; border:none; color:#58a6ff; cursor:pointer; text-decoration:underline;">Reiniciar Laboratorio</button>
            </div>
        </div>
    ''', levels=LEVELS, progress=session['progress'])

# Ruta dinámica para cada nivel
@app.route('/level/<int:level_id>', methods=['GET', 'POST'])
def level(level_id):
    init_session()
    
    # Si el nivel no existe, lo mandamos al mapa principal
    if level_id not in LEVELS: return redirect(url_for('dashboard'))
    
    # BLOQUEO DE SEGURIDAD: No puedes entrar a un nivel si no pasaste el anterior
    # Esto obliga al estudiante a seguir el orden lógico
    if level_id > 1 and (level_id - 1) not in session['progress']:
        return redirect(url_for('dashboard'))

    lv = LEVELS[level_id]
    is_completed = level_id in session['progress']
    results = []
    error_msg = None
    query_str = ""
    
    # Cuando el estudiante envía una respuesta (hace clic en Ejecutar)
    if request.method == 'POST':
        session['total_attempts'] += 1
        input_val = request.form.get('input', '')
        
        # --- LÓGICA DE VALIDACIÓN (Detección de Exploits) ---
        try:
            if level_id <= 4: # Estás en la fase de SQL Injection
                conn = get_db_connection()
                # ¡VULNERABILIDAD INTENCIONAL!: Concatenamos el input directamente en el SQL
                # Esto permite que el estudiante inyecte sus propios comandos
                query_str = f"SELECT username, role FROM users WHERE username = '{input_val}'"
                results = conn.execute(query_str).fetchall()
                conn.close()
                
                if level_id == 1: # Victoria si devolviste más de una fila (un Bypass)
                    if len(results) > 1: is_completed = True
                elif level_id == 2: # Victoria si el input rompió la consulta (un Error)
                    pass # La validación real ocurre abajo en el 'except'
                elif level_id == 3: # Victoria si usó lógica booleana AND/OR
                    if any("admin" in str(r['username']) for r in results) and ("AND" in input_val.upper() or "OR" in input_val.upper()):
                        is_completed = True
                elif level_id == 4: # Victoria si extrajo el Flag final de la tabla identidad
                    for row in results:
                        if any("CTF{sqli_completo_2026}" in str(row[k]) for k in row.keys()):
                            is_completed = True
                            
            elif level_id == 5: # Estás en la fase de Directory Traversal
                # ¡VULNERABILIDAD INTENCIONAL!: Unimos la ruta sin sanear el nombre del archivo
                filepath = os.path.join('docs', input_val)
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        content = f.read()
                        results = [{"file": input_val, "content": content}]
                        # Victoria si logró leer el flag que está fuera de 'docs'
                        if "CTF{traversal_completo_2026}" in content: is_completed = True
        
        except Exception as e:
            # Si hay un error de SQL y estamos en el Nivel 2, entonces ganó el reto de error
            error_msg = str(e)
            if level_id == 2: is_completed = True

        # Si descubrió la vulnerabilidad, guardamos su progreso
        if is_completed and level_id not in session['progress']:
            session['progress'].append(level_id)
            session.modified = True

    return render_template_string(BASE_STYLE + '''
        <div class="nav">
            <a href="/" style="color: var(--primary); text-decoration: none;">← Volver al Mapa</a>
            <div style="font-weight: bold;">{{ lv.title }}</div>
            <a href="/results" class="btn btn-abandon" style="padding: 5px 15px;">Abandonar</a>
        </div>
        <div class="container" style="text-align: left;">
            <h2>Objetivo:</h2>
            <p>{{ lv.objective }}</p>
            
            <form method="POST" style="background: #161b22; padding: 20px; border-radius: 12px; margin: 20px 0;">
                <label>{{ 'Nombre de Usuario:' if level_id < 5 else 'Nombre de Archivo:' }}</label><br>
                <input type="text" name="input" style="width: 70%; padding: 10px; margin: 10px 0; background:#000; color:#fff; border:1px solid #30363d; border-radius: 8px;">
                <button type="submit" class="btn btn-primary" style="margin-top:0;">Ejecutar</button>
            </form>

            {% if query_str %} <p style="font-size: 0.8rem; opacity: 0.5;">Debug Query: <code>{{ query_str }}</code></p> {% endif %}

            {% if error_msg %}
                <div style="background: rgba(244,63,94,0.1); border: 1px solid var(--accent); padding: 15px; border-radius: 8px; color: var(--accent);">
                    <strong>Error del Motor:</strong> {{ error_msg }}
                </div>
            {% endif %}

            {% if results %}
                <table>
                    <tr>
                        {% for key in results[0].keys() %} <th>{{ key|capitalize }}</th> {% endfor %}
                    </tr>
                    {% for row in results %}
                    <tr>
                        {% for key in row.keys() %} <td>{{ row[key] }}</td> {% endfor %}
                    </tr>
                    {% endfor %}
                </table>
            {% endif %}

            {% if not completed %}
                <details class="hint-box">
                    <summary style="font-weight: bold; cursor: pointer; color: var(--primary);">💡 Obtener una Pista</summary>
                    <p style="margin-top:10px; font-size: 0.95rem;">{{ lv.hint|safe }}</p>
                </details>
            {% else %}
                <div class="success-panel">
                    <h3 style="color: var(--success); margin-top:0;">🎉 ¡Nivel Completado!</h3>
                    <p><strong>Explicación:</strong> {{ lv.explanation }}</p>
                    <p><strong>🛡️ Defensa:</strong> {{ lv.prevention }}</p>
                    <div style="text-align: right;">
                        {% if level_id < 5 %}
                        <a href="/level/{{level_id + 1}}" class="btn btn-primary">Ir al Siguiente Nivel →</a>
                        {% else %}
                        <a href="/results" class="btn btn-primary">Ver Resultados Finales ⭐</a>
                        {% endif %}
                    </div>
                </div>
            {% endif %}
        </div>
    ''', lv=lv, query_str=query_str, error_msg=error_msg, results=results, completed=is_completed, level_id=level_id)

@app.route('/results')
def results():
    init_session()
    score = len(session['progress'])
    total = len(LEVELS)
    percent = (score / total) * 100
    
    return render_template_string(BASE_STYLE + '''
        <div class="container" style="background: var(--card); padding: 50px; border-radius: 30px; margin-top: 80px;">
            <h1 style="font-size: 3rem;">Ficha de Resultados</h1>
            <div style="font-size: 1.5rem; margin: 20px 0;">Logros Desbloqueados: <span style="color: var(--primary);">{{ score }} / {{ total }}</span></div>
            
            <div style="width: 100%; background: #30363d; height: 12px; border-radius: 6px; margin: 30px 0; overflow:hidden;">
                <div style="width: {{ percent }}%; background: var(--primary); height: 100%; transition: width 1s;"></div>
            </div>

            <div style="text-align: left; margin-top: 40px; border-top: 1px solid #30363d; padding-top: 20px;">
                <h3>Logros Obtenidos:</h3>
                {% for id in range(1, total + 1) %}
                    <div style="margin: 10px 0; display: flex; align-items: center; gap: 15px; opacity: {{ 1 if id in progress else 0.3 }}">
                        <span style="font-size: 1.5rem;">{{ '✅' if id in progress else '🔒' }}</span>
                        <span>{{ levels[id].title }}</span>
                    </div>
                {% endfor %}
            </div>

            <div style="margin-top: 40px; display: flex; gap: 20px; justify-content: center;">
                <a href="/" class="btn btn-primary">Volver al Laboratorio</a>
                <a href="/reset" class="btn btn-abandon">Reiniciar de Cero</a>
            </div>
        </div>
    ''', score=score, total=total, percent=percent, progress=session['progress'], levels=LEVELS)

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
