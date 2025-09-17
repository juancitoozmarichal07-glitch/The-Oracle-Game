#backend/main.py

import sys
import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIGURACIÓN DE LA APLICACIÓN Y CORS ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# --- PREPARAR EL CAMINO A LOS MÓDULOS ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- IMPORTAR E INICIALIZAR EL CEREBRO Y TODOS LOS SKILLSETS ---
from ale_core import ALE_Core
from skillsets.guardian import Guardian
from skillsets.oracle import Oracle
from skillsets.veridian import Veridian  # <-- IMPORTANTE

# 1. Creamos la instancia del motor A.L.E.
ale = ALE_Core()

# 2. Cargamos TODOS los skillsets en el motor.
print("Cargando skillsets en el motor A.L.E...")
ale.cargar_skillset("guardian", Guardian()) # <-- IMPORTANTE
ale.cargar_skillset("oracle", Oracle())
ale.cargar_skillset("veridian", Veridian()) # <-- IMPORTANTE

print("✅ Servidor listo. A.L.E. está online con los skillsets Guardian, Oracle y Veridian.")

# --- DEFINIR LA RUTA DE EJECUCIÓN ---
@app.route('/execute', methods=['POST'])
def handle_execution():
    datos_peticion = request.json
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    respuesta_de_ale = loop.run_until_complete(ale.procesar_peticion(datos_peticion))
    return jsonify(respuesta_de_ale)

# --- ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
