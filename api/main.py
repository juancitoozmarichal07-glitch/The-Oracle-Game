# backend/main.py (Versión Final con todos los Skillsets)
import sys
import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ale_core import ALE_Core
from skillsets.guardian import Guardian
from skillsets.oracle import Oracle
from skillsets.veridian import Veridian
from skillsets.akinator import Akinator

ale = ALE_Core()

print("Cargando skillsets en el motor A.L.E...")
ale.cargar_skillset("guardian", Guardian())
ale.cargar_skillset("oracle", Oracle())
ale.cargar_skillset("veridian", Veridian())
ale.cargar_skillset("akinator", Akinator())

print("✅ Servidor listo. A.L.E. está online con los skillsets Guardian, Oracle, Veridian y Akinator.")

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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
