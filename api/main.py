# =================================================================
# == MAIN.PY - EDICIÓN EXCLUSIVA PARA "THE ORACLE GAME"          ==
# =================================================================
# - Este archivo está optimizado para cargar únicamente el skillset
#   necesario para el juego, evitando dependencias innecesarias.

import sys
import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- 1. CONFIGURACIÓN DE LA APLICACIÓN Y CORS ---
# Se crea la aplicación Flask y se configuran los permisos (CORS)
# para permitir que tu frontend (en Vercel) pueda comunicarse con este backend.
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def after_request(response):
    # Añade cabeceras de seguridad para una comunicación fluida
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# --- 2. PREPARAR EL CAMINO A LOS MÓDULOS ---
# Esto asegura que Python pueda encontrar tus otros archivos .py (ale_core, oracle)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- 3. IMPORTAR E INICIALIZAR SOLO LO NECESARIO ---
# Se importa el motor principal y ÚNICAMENTE el skillset del Oráculo.
from ale_core import ALE_Core
from skillsets.oracle import Oracle

# 3.1. Se crea la instancia del motor A.L.E.
ale = ALE_Core()

# 3.2. Se carga el skillset 'oracle' en el motor.
print("Cargando skillset 'Oracle' en el motor A.L.E...")
ale.cargar_skillset("oracle", Oracle())

print("✅ Servidor listo. A.L.E. está online exclusivamente para The Oracle Game.")

# --- 4. DEFINIR LA RUTA DE LA API ---
# Esta es la "puerta" donde el frontend enviará las peticiones.
@app.route('/execute', methods=['POST'])
def handle_execution():
    datos_peticion = request.json
    
    # Este bloque gestiona el 'event loop' de asyncio, crucial para
    # que las funciones 'async' de tu skillset funcionen dentro de Flask.
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Se procesa la petición y se espera el resultado del Oráculo.
    respuesta_de_ale = loop.run_until_complete(ale.procesar_peticion(datos_peticion))
    
    # Se devuelve la respuesta al frontend en formato JSON.
    return jsonify(respuesta_de_ale)

# --- 5. PUNTO DE ARRANQUE (PARA PRUEBAS LOCALES) ---
# Este bloque solo se ejecuta si corres 'python main.py' en tu PC.
# Gunicorn (en Render) ignora esta parte y usa la variable 'app' directamente.
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

