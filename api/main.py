# =================================================================
# == MAIN.PY - EDICIÓN COMPLETA PARA VERCEL                      ==
# =================================================================
# - Esta versión carga TODOS los skillsets (Guardian, Oracle,
#   Veridian, Akinator) para una funcionalidad completa.

import sys
import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIGURACIÓN DE LA APLICACIÓN Y CORS ---
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- PREPARAR EL CAMINO A LOS MÓDULOS ---
# Esto asegura que Python pueda encontrar 'ale_core' y 'skillsets'
# cuando Vercel ejecute el script desde la raíz del proyecto.
# (Esta configuración es robusta para el entorno de Vercel)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

# --- IMPORTAR E INICIALIZAR TODOS LOS SKILLSETS ---
from api.ale_core import ALE_Core
from api.skillsets.guardian import Guardian
from api.skillsets.oracle import Oracle
from api.skillsets.veridian import Veridian
from api.skillsets.akinator import Akinator

# 1. Creamos la instancia del motor A.L.E.
ale = ALE_Core()

# 2. Cargamos TODOS los skillsets en el motor.
print("Cargando skillsets en el motor A.L.E...")
ale.cargar_skillset("guardian", Guardian())
ale.cargar_skillset("oracle", Oracle())
ale.cargar_skillset("veridian", Veridian())
ale.cargar_skillset("akinator", Akinator())

print("✅ Servidor listo. A.L.E. está online con los skillsets Guardian, Oracle, Veridian y Akinator.")

# --- DEFINIR LA RUTA DE EJECUCIÓN ---
# Vercel redirigirá las peticiones de /api/execute a esta función.
@app.route('/api/execute', methods=['POST'])
def handle_execution():
    datos_peticion = request.json
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    respuesta_de_ale = loop.run_until_complete(ale.procesar_peticion(datos_peticion))
    
    return jsonify(respuesta_de_ale)

# --- PUNTO DE ARRANQUE (Vercel lo ignora) ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
