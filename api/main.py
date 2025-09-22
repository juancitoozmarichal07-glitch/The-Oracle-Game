# =================================================================
# == MAIN.PY - EDICIÓN "BACKEND PURO" PARA RENDER (CORS CORREGIDO) ==
# =================================================================
import sys
import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIGURACIÓN DE LA APLICACIÓN Y CORS ---
app = Flask(__name__)

# ===================================================================
# ===       ¡AQUÍ ESTÁ LA CORRECCIÓN PARA EL ERROR DE CORS!       ===
# ===================================================================
# En lugar de permitir '*', le damos permiso explícito y único a tu
# dominio de Vercel. Esto es más seguro y evita bloqueos.
CORS(app, resources={
    r"/execute": {
        "origins": "https://the-oracle-game-ny7nyna98-juan-s-projects-1a87dbe4.vercel.app"
    }
})

@app.after_request
def after_request(response):
    # Estas cabeceras son importantes, las mantenemos.
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# --- PREPARAR EL CAMINO A LOS MÓDULOS ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- INICIALIZAR EL CEREBRO ---
from ale_core import ALE_Core
from skillsets.oracle import Oracle
ale = ALE_Core()
ale.cargar_skillset("oracle", Oracle())
print("✅ Servidor de API listo. A.L.E. está online para The Oracle Game.")

# --- RUTA DE LA API ---
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

# --- PUNTO DE ARRANQUE (Gunicorn lo ignora, útil para pruebas locales) ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
