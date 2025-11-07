# main.py - VERSIÓN FINALÍSIMA (Anti-Gunicorn-Workers)

import os
import sys
import asyncio
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- FUNCIÓN PARA CREAR LA APLICACIÓN (LA SOLUCIÓN DEFINITIVA) ---
def create_app():
    app = Flask(__name__)
    CORS(app)

    # --- 1. CONFIGURACIÓN DE RUTA (DENTRO DE LA FUNCIÓN) ---
    # Esto asegura que los imports funcionen siempre, sin importar cómo Gunicorn llame al worker.
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..'))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        print("✅ Rutas del proyecto configuradas en el contexto de la app.")
    except Exception as e:
        print(f"🚨 Error configurando rutas: {e}")
        sys.exit(1)

    # --- 2. IMPORTACIÓN Y CARGA DE SKILLSETS (DENTRO DE LA FUNCIÓN) ---
    # Al estar aquí, se cargan en el momento correcto, siempre.
    try:
        from api.skillsets.oracle import Oracle
        from api.skillsets.akinator import Akinator
        
        skillsets_cargados = {
            "oracle": Oracle(),
            "akinator": Akinator()
        }
        print(f"✅ Motor listo con skillsets: {list(skillsets_cargados.keys())}")
    except ModuleNotFoundError as e:
        print(f"🚨 ERROR FATAL: No se encontró un archivo de skillset: {e}")
        sys.exit(1)


    # --- 3. RUTA DE LA API (CON LA CORRECCIÓN DE ASYNCIO) ---
    @app.route('/api/execute', methods=['POST', 'OPTIONS'])
    async def api_execute():
        if request.method == 'OPTIONS':
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
            skillset_instance = skillsets_cargados.get(target_skillset)

            if not skillset_instance:
                return jsonify({"error": f"Skillset '{target_skillset}' no encontrado."}), 404

            respuesta = await skillset_instance.ejecutar(datos_peticion)
            return jsonify(respuesta)

        except Exception as e:
            print(f"🚨 ERROR INESPERADO en /api/execute: {e}")
            traceback.print_exc()
            return jsonify({"error": "Error interno del servidor."}), 500

    # --- 4. RUTA DE VERIFICACIÓN ---
    @app.route('/')
    def index():
        return "<h1>El motor de la API está vivo y coleando.</h1>"

    return app

# --- 5. PUNTO DE ENTRADA PARA GUNICORN ---
# Gunicorn buscará y usará esta variable 'app'.
app = create_app()

print("✅ Aplicación Flask creada y lista para ser servida por Gunicorn.")
