# ===================================================================
# ==         MAIN.PY - VERSIÓN ESENCIAL Y ROBUSTA                ==
# ===================================================================
# - OBJETIVO: Funcionar en Render de forma limpia y estable.
# - MINIMALISTA: Solo carga los skillsets y expone la API.
# - A PRUEBA DE BALAS: Configuración de CORS y rutas estándar.
# ===================================================================

import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- 1. CONFIGURACIÓN DE RUTA ---
# Asegura que Python encuentre la carpeta 'skillsets' desde Render.
try:
    # Obtiene la ruta del directorio actual (donde está main.py, es decir, /api)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Sube un nivel para llegar a la raíz del proyecto
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    # Añade la raíz del proyecto al path de Python
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception:
    # Si esto falla, la aplicación no puede arrancar.
    sys.exit("Error crítico: No se pudieron configurar las rutas del proyecto.")

# --- 2. IMPORTACIÓN DE SKILLSETS ---
# Importamos los skillsets usando la ruta relativa desde la raíz.
try:
    from skillsets.oracle import Oracle
    from skillsets.akinator import Akinator
except ModuleNotFoundError:
    sys.exit("Error crítico: No se encontró 'oracle.py' o 'akinator.py' en 'api/skillsets/'.")


# --- 3. INICIALIZACIÓN DE FLASK Y CORS ---
app = Flask(__name__)
# Habilita CORS para todas las rutas y orígenes. Es la configuración más permisiva.
CORS(app)


# --- 4. CARGA DE LOS SKILLSETS ---
# Creamos las instancias de nuestros skillsets.
try:
    skillsets_cargados = {
        "oracle": Oracle(),
        "akinator": Akinator()
    }
except Exception as e:
    sys.exit(f"Error crítico al inicializar un skillset: {e}")


# --- 5. RUTA PRINCIPAL DE LA API ---
# Esta es la ruta que tu juego llamará. Es asíncrona para ser compatible con tus skillsets.
@app.route('/api/execute', methods=['POST'])
async def api_execute():
    try:
        datos_peticion = request.get_json()
        if not datos_peticion:
            return jsonify({"error": "Petición sin cuerpo JSON."}), 400

        target_skillset = datos_peticion.get("skillset_target")
        skillset_instance = skillsets_cargados.get(target_skillset)

        if not skillset_instance:
            return jsonify({"error": f"Skillset '{target_skillset}' no encontrado."}), 404

        # Ejecutamos el skillset de forma asíncrona
        respuesta = await skillset_instance.ejecutar(datos_peticion)
        return jsonify(respuesta)

    except Exception as e:
        # Si algo falla dentro de la ejecución, devolvemos un error 500.
        return jsonify({"error": "Error interno del servidor.", "detalle": str(e)}), 500


# --- 6. RUTA DE VERIFICACIÓN DE SALUD ---
# Render usará esta ruta para saber si tu servicio está vivo.
@app.route('/')
def health_check():
    return "<h1>API Engine is alive.</h1>"

# --- 7. PUNTO DE ENTRADA (SOLO PARA PRUEBAS LOCALES) ---
# Render ignorará esto y usará el "Start Command" que le dimos.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

