# ===================================================================
# ==         MAIN.PY - VERSIÓN FINAL ANTI-ERRORES                ==
# ===================================================================
# - CORREGIDO: Conflicto de Asyncio con Gunicorn.
# - LIMPIO: Carga únicamente los skillsets que existen.
# - ROBUSTO: Configuración de rutas y CORS a prueba de balas.
# - LISTO PARA RENDER.
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
    print("✅ Rutas del proyecto configuradas.")
except Exception as e:
    print(f"🚨 Error configurando rutas: {e}")
    sys.exit(1)

# --- 2. IMPORTACIÓN DE SKILLSETS (SOLO LO QUE EXISTE) ---
try:
    from api.skillsets.oracle import Oracle
    from api.skillsets.akinator import Akinator
    print("✅ Skillsets 'Oracle' y 'Akinator' importados correctamente.")
except ModuleNotFoundError as e:
    print(f"🚨 ERROR FATAL: No se encontró un archivo de skillset: {e}")
    print("   Asegúrate de que 'oracle.py' y 'akinator.py' están en 'api/skillsets'.")
    sys.exit(1)

# --- 3. INICIALIZACIÓN DE FLASK Y CORS ---
app = Flask(__name__)
CORS(app) # Habilitamos CORS para toda la aplicación
print("✅ Flask y CORS inicializados.")

# --- 4. MOTOR SIMPLE Y DIRECTO ---
skillsets_cargados = {
    "oracle": Oracle(),
    "akinator": Akinator()
}
print(f"✅ Motor listo con skillsets: {list(skillsets_cargados.keys())}")

# --- 5. RUTA DE LA API (CON LA CORRECCIÓN DE ASYNCIO) ---
@app.route('/', methods=['POST', 'OPTIONS'])
async def api_execute():
    if request.method == 'OPTIONS':
        # Manejo correcto de la petición pre-vuelo de CORS
        return ('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })

    try:
        datos_peticion = request.get_json()
        if not datos_peticion:
            return jsonify({"error": "Petición sin JSON."}), 400

        target_skillset = datos_peticion.get("skillset_target")
        print(f"-> Petición para: '{target_skillset}'")

        skillset_instance = skillsets_cargados.get(target_skillset)
        if not skillset_instance:
            return jsonify({"error": f"Skillset '{target_skillset}' no encontrado."}), 404

        # ¡¡¡LA CORRECCIÓN CLAVE!!!
        # Usamos 'await' directamente, que es la forma correcta en Flask > 2.0
        respuesta = await skillset_instance.ejecutar(datos_peticion)
        return jsonify(respuesta)

    except Exception as e:
        print(f"🚨 ERROR INESPERADO en /api/execute: {e}")
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor."}), 500

# --- 6. RUTA DE VERIFICACIÓN (para saber si el servidor está vivo) ---
@app.route('/')
def index():
    return "<h1>El motor de la API está vivo.</h1>"

# --- 7. PUNTO DE ENTRADA PARA GUNICORN ---
# Gunicorn buscará y usará esta variable 'app'. No se necesita más.
print("✅ Aplicación Flask lista para ser servida por Gunicorn.")

