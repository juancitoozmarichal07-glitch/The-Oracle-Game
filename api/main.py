# ===================================================================
# ==         MAIN.PY - VERSIÓN ANTI-ERRORES (FINAL)              ==
# ===================================================================
# - NO MÁS ERRORES DE IMPORTACIÓN.
# - CARGA ÚNICAMENTE ORACLE Y AKINATOR.
# - LISTO PARA DESPLEGAR EN RENDER.
# ===================================================================

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio

# --- 1. CONFIGURACIÓN DE RUTA ---
# Esto asegura que Python encuentre la carpeta 'skillsets'
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # La ruta correcta a la raíz del proyecto desde api/main.py es un nivel arriba
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    # Añadimos también la carpeta 'api' para asegurar las importaciones relativas
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    print("✅ Rutas del proyecto configuradas correctamente.")
except Exception as e:
    print(f"🚨 Error configurando las rutas: {e}")
    sys.exit(1)

# --- 2. IMPORTACIÓN DE SKILLSETS (LA ÚNICA VERDAD) ---
# Importamos SOLO lo que existe. Si uno de estos falla, el problema está en el archivo del skillset.
try:
    from skillsets.oracle import Oracle
    from skillsets.akinator import Akinator
    print("✅ Skillsets 'Oracle' y 'Akinator' importados.")
except ModuleNotFoundError as e:
    print(f"🚨 ERROR FATAL: No se encontró un archivo de skillset esencial: {e}")
    print("   Asegúrate de que 'oracle.py' y 'akinator.py' están dentro de la carpeta 'api/skillsets'.")
    sys.exit(1)
except Exception as e:
    print(f"🚨 ERROR FATAL al importar un skillset: {e}")
    sys.exit(1)


# --- 3. INICIALIZACIÓN DE FLASK Y CORS ---
app = Flask(__name__)
# Configuración de CORS para permitir peticiones desde cualquier frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})
print("✅ Flask y CORS inicializados.")


# --- 4. MOTOR SIMPLE DE SKILLSETS ---
# No usamos clases complicadas, vamos a lo directo.
skillsets_cargados = {
    "oracle": Oracle(),
    "akinator": Akinator()
}
print(f"✅ Motor listo con los siguientes skillsets: {list(skillsets_cargados.keys())}")


# --- 5. RUTA DE LA API ---
@app.route('/api/execute', methods=['POST', 'OPTIONS'])
async def api_execute():
    # Manejo de la petición pre-vuelo (necesaria para CORS)
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        return ('', 204, headers)

    # Procesamiento de la petición POST
    try:
        datos_peticion = request.get_json()
        if not datos_peticion:
            return jsonify({"error": "La petición no contiene un JSON válido."}), 400

        target_skillset = datos_peticion.get("skillset_target")
        print(f"-> Petición recibida para el skillset: '{target_skillset}'")

        skillset_instance = skillsets_cargados.get(target_skillset)
        if not skillset_instance:
            return jsonify({"error": f"El skillset '{target_skillset}' no existe."}), 404

        if hasattr(skillset_instance, 'ejecutar'):
            respuesta = await skillset_instance.ejecutar(datos_peticion)
            return jsonify(respuesta)
        else:
            return jsonify({"error": f"El skillset '{target_skillset}' no tiene un método 'ejecutar'."}), 500

    except Exception as e:
        print(f"🚨 ERROR INESPERADO en /api/execute: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor."}), 500

# --- 6. PUNTO DE ENTRADA PARA GUNICORN ---
# Gunicorn buscará y usará esta variable 'app'. No necesitamos el if __name__ == "__main__".
print("✅ Aplicación Flask lista para ser servida por Gunicorn.")

