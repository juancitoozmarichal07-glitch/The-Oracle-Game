# api/main.py - v41.0 "Arquitectura Anti-Bloqueo"
# Se saca la carga de los skillsets fuera de la Application Factory para
# evitar "deadlocks" en Gunicorn durante el deploy.

import sys
import os
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- 1. CONFIGURACIÓN DE RUTA Y CARGA DE SKILLSETS (ÁMBITO GLOBAL) ---
# Se ejecuta UNA SOLA VEZ cuando Gunicorn importa el archivo.
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.append(project_root)
    print("✅ Ruta del proyecto configurada.")

    # ¡CARGA PESADA AQUÍ! Fuera de la factory.
    from api.skillsets.oracle import Oracle
    from api.skillsets.akinator import Akinator
    print("✅ Componentes de skillsets importados.")

    # Creamos las instancias de los skillsets UNA SOLA VEZ.
    SKILLSETS_LISTOS = {
        "oracle": Oracle(),
        "akinator": Akinator()
    }
    print(f"✅ Motor listo con skillsets: {list(SKILLSETS_LISTOS.keys())}")

except Exception as e:
    print(f"🚨 ERROR FATAL DURANTE LA CARGA INICIAL: {e}")
    traceback.print_exc()
    # Si esto falla, el deploy se detendrá con un error claro.
    sys.exit(1)


# --- 2. FUNCIÓN PARA CREAR LA APP (AHORA MÁS LIGERA) ---
def create_app(skillsets_precargados):
    app = Flask(__name__)
    CORS(app)

    print("🔧 Creando instancia de la aplicación Flask...")

    # --- RUTAS DE LA APLICACIÓN ---
    @app.route('/')
    def index():
        return "<h1>Motor A.L.E. v41.0 (Anti-Bloqueo) está online.</h1>"

    @app.route('/api/execute', methods=['POST', 'OPTIONS'])
    async def api_execute():
        if request.method == 'OPTIONS':
            return ('', 204)
            
        try:
            datos_peticion = request.get_json()
            if not datos_peticion:
                return jsonify({"error": "Petición sin JSON."}), 400

            target_skillset = datos_peticion.get("skillset_target")
            # Usa la lista de skillsets que ya estaba cargada.
            skillset_instance = skillsets_precargados.get(target_skillset)

            if not skillset_instance:
                return jsonify({"error": f"Skillset '{target_skillset}' no encontrado."}), 404

            respuesta = await skillset_instance.ejecutar(datos_peticion)
            return jsonify(respuesta)

        except Exception as e:
            print(f"🚨 ERROR INESPERADO en /api/execute: {e}")
            traceback.print_exc()
            return jsonify({"error": "Error interno del servidor."}), 500

    print("✅ Aplicación Flask creada y rutas configuradas.")
    return app

# --- 3. PUNTO DE ENTRADA PARA GUNICORN ---
# Creamos la app pasándole los skillsets que ya están en memoria.
app = create_app(SKILLSETS_LISTOS)

# Esta parte solo se usa para pruebas locales.
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

