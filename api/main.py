# api/main.py - v40.0 "El Regreso del Async Correcto"
# Se restaura la estructura de Application Factory y 'async def' en la ruta
# para eliminar el fatal 'RuntimeError: You cannot use AsyncToSync...'.

import sys
import os
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- 1. CONFIGURACIÓN DE RUTA DEL PROYECTO ---
# Esto asegura que Python siempre encuentre la carpeta 'skillsets'
try:
    # Obtenemos el directorio donde está main.py (que es 'api/')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Subimos un nivel para llegar a la raíz del proyecto
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.append(project_root)
    print("✅ Ruta del proyecto configurada.")
except Exception as e:
    print(f"🚨 Error configurando rutas: {e}")
    sys.exit(1)

# --- FUNCIÓN PARA CREAR Y CONFIGURAR LA APP (Application Factory) ---
def create_app():
    app = Flask(__name__)
    CORS(app)

    # --- IMPORTACIÓN Y CARGA DE SKILLSETS (Dentro de la factory) ---
    try:
        from api.skillsets.oracle import Oracle
        from api.skillsets.akinator import Akinator
        print("✅ Componentes importados en el contexto de la app.")

        skillsets_cargados = {
            "oracle": Oracle(),
            "akinator": Akinator()
        }
        print(f"✅ Motor listo con skillsets: {list(skillsets_cargados.keys())}")

    except ModuleNotFoundError as e:
        print(f"🚨 ERROR DE IMPORTACIÓN: {e}")
        print("   Asegúrate de que la estructura de carpetas es correcta.")
        sys.exit()

    # --- RUTAS DE LA APLICACIÓN ---
    @app.route('/')
    def index():
        return "<h1>Motor A.L.E. v40.0 está online.</h1>"

    # ¡¡¡LA RUTA ASÍNCRONA CORRECTA!!!
    @app.route('/api/execute', methods=['POST', 'OPTIONS'])
    async def api_execute():
        if request.method == 'OPTIONS':
            # Manejo de la petición pre-vuelo CORS
            return ('', 204)
            
        try:
            datos_peticion = request.get_json()
            if not datos_peticion:
                return jsonify({"error": "Petición sin JSON."}), 400

            target_skillset = datos_peticion.get("skillset_target")
            skillset_instance = skillsets_cargados.get(target_skillset)

            if not skillset_instance:
                return jsonify({"error": f"Skillset '{target_skillset}' no encontrado."}), 404

            # ¡Llamada directa con await! ¡Sin asyncio.run!
            respuesta = await skillset_instance.ejecutar(datos_peticion)
            return jsonify(respuesta)

        except Exception as e:
            print(f"🚨 ERROR INESPERADO en /api/execute: {e}")
            traceback.print_exc()
            return jsonify({"error": "Error interno del servidor."}), 500

    print("✅ Aplicación Flask creada y lista para ser servida por Gunicorn.")
    return app

# --- PUNTO DE ENTRADA PARA GUNICORN ---
# Gunicorn buscará esta variable 'app' por defecto.
app = create_app()

# Esta parte solo se ejecuta si corres 'python api/main.py' localmente
if __name__ == "__main__":
    print("-" * 40)
    print("🚀 Iniciando servidor Flask en modo local (debug)...")
    print("-" * 40)
    app.run(host='0.0.0.0', port=5000, debug=True)
