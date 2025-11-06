# ===================================================================
# ==         MAIN.PY - VERSIÓN DE DEPURACIÓN TOTAL               ==
# ===================================================================
# - OBJETIVO: Encontrar el error final en Render.
# - LOGGING AGRESIVO: Cada paso se imprime en la consola.
# - CAPTURA DE ERRORES: Un bloque try/except gigante para que nada se escape.
# ===================================================================

import os
import sys
import asyncio
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- 1. CONFIGURACIÓN DE RUTA (A PRUEBA DE BALAS) ---
# Esto asegura que Python siempre encuentre la carpeta 'skillsets'
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    print("✅ [LOG] Rutas del proyecto configuradas correctamente.")
except Exception as e:
    print(f"🚨 [ERROR CRÍTICO] Fallo al configurar las rutas del sistema: {e}")
    sys.exit(1)

# --- 2. IMPORTACIÓN DE SKILLSETS (SOLO LO QUE EXISTE) ---
try:
    from api.skillsets.oracle import Oracle
    from api.skillsets.akinator import Akinator
    print("✅ [LOG] Skillsets 'Oracle' y 'Akinator' importados correctamente.")
except ModuleNotFoundError as e:
    print(f"🚨 [ERROR CRÍTICO] No se encontró un archivo de skillset: {e}")
    print("   Asegúrate de que 'oracle.py' y 'akinator.py' están en 'api/skillsets'.")
    sys.exit(1)
except Exception as e:
    print(f"🚨 [ERROR CRÍTICO] Fallo inesperado al importar skillsets: {e}")
    sys.exit(1)


# --- 3. INICIALIZACIÓN DE FLASK Y CORS ---
app = Flask(__name__)
# Habilitamos CORS para toda la aplicación, aceptando peticiones de cualquier origen.
CORS(app, resources={r"/*": {"origins": "*"}})
print("✅ [LOG] Flask y CORS inicializados.")

# --- 4. MOTOR SIMPLE Y DIRECTO ---
try:
    skillsets_cargados = {
        "oracle": Oracle(),
        "akinator": Akinator()
    }
    print(f"✅ [LOG] Motor listo con skillsets: {list(skillsets_cargados.keys())}")
except Exception as e:
    print(f"🚨 [ERROR CRÍTICO] Fallo al inicializar los skillsets: {e}")
    traceback.print_exc()
    # Continuamos para que la app al menos arranque y podamos ver otros errores.
    skillsets_cargados = {}


# --- 5. RUTA DE LA API (CON SÚPER-DEPURACIÓN) ---
@app.route('/api/execute', methods=['POST', 'OPTIONS'])
async def api_execute():
    print("\n--- [LOG] INICIO DE PETICIÓN A /api/execute ---")

    if request.method == 'OPTIONS':
        print("-> [LOG] Recibida petición OPTIONS (pre-vuelo CORS). Respondiendo OK.")
        return ('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })

    try:
        print("-> [LOG] Recibida petición POST. Procesando...")
        
        # Verificamos los headers para depuración
        print(f"-> [LOG] Headers de la petición: {request.headers}")

        datos_peticion = request.get_json()
        if not datos_peticion:
            print("🚨 [ERROR] La petición no contenía un cuerpo JSON válido.")
            return jsonify({"error": "Petición sin JSON."}), 400

        print(f"-> [LOG] Cuerpo JSON recibido: {datos_peticion}")

        target_skillset = datos_peticion.get("skillset_target")
        print(f"-> [LOG] Petición para el skillset: '{target_skillset}'")

        skillset_instance = skillsets_cargados.get(target_skillset)
        if not skillset_instance:
            print(f"🚨 [ERROR] Skillset '{target_skillset}' no encontrado en la lista de skillsets cargados.")
            return jsonify({"error": f"Skillset '{target_skillset}' no encontrado."}), 404

        print(f"-> [LOG] Ejecutando el skillset '{target_skillset}'...")
        respuesta = await skillset_instance.ejecutar(datos_peticion)
        print(f"-> [LOG] Skillset ejecutado. Respuesta obtenida (primeros 200 chars): {str(respuesta)[:200]}...")
        
        print("-> [LOG] Enviando respuesta JSON al cliente.")
        return jsonify(respuesta)

    except Exception as e:
        # ESTE ES EL BLOQUE MÁS IMPORTANTE
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!!      ERROR CATASTRÓFICO EN /api/execute      !!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"TIPO DE ERROR: {type(e).__name__}")
        print(f"MENSAJE DE ERROR: {e}")
        print("--- TRACEBACK COMPLETO ---")
        traceback.print_exc()
        print("--------------------------\n")
        return jsonify({"error": "Error interno del servidor. Revisa los logs de Render."}), 500

# --- 6. RUTA DE VERIFICACIÓN (para saber si el servidor está vivo) ---
@app.route('/')
def index():
    print("-> [LOG] Petición a la ruta raíz ('/'). Respondiendo que el motor está vivo.")
    return "<h1>El motor de la API está vivo y en modo DEPURACIÓN.</h1>"

# --- 7. PUNTO DE ENTRADA PARA EL SERVIDOR ---
if __name__ == '__main__':
    # Esto es solo para pruebas locales, Render usará el "Start Command"
    print("⚠️ [AVISO] Ejecutando en modo de desarrollo local de Flask.")
    app.run(host='0.0.0.0', port=8080, debug=True)
else:
    print("✅ [LOG] Aplicación Flask lista para ser servida por un servidor de producción (Gunicorn/Flask).")

