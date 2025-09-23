# =================================================================
# == MAIN.PY - EDICIÓN "ORACLE GAME" PARA VERCEL (CON AKINATOR)  ==
# =================================================================
# - Esta versión importa y carga los skillsets para ambos modos de
#   juego: Oracle y Clásico (Akinator).

import sys
import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIGURACIÓN DE LA APLICACIÓN Y CORS ---
app = Flask(__name__)
# Permitimos que cualquier origen hable con nuestra API.
# Vercel gestionará la seguridad.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- PREPARAR EL CAMINO A LOS MÓDULOS ---
# Esto asegura que Python pueda encontrar 'ale_core' y 'skillsets'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- IMPORTAR E INICIALIZAR EL CEREBRO (ORACLE Y AKINATOR) ---
from ale_core import ALE_Core
from skillsets.oracle import Oracle
from skillsets.akinator import Akinator  # <-- CAMBIO 1: Importamos el nuevo skillset

# 1. Creamos la instancia del motor A.L.E.
ale = ALE_Core()

# 2. Cargamos AMBOS skillsets para los dos modos de juego.
print("Cargando skillsets en el motor A.L.E...")
ale.cargar_skillset("oracle", Oracle())
ale.cargar_skillset("akinator", Akinator()) # <-- CAMBIO 2: Cargamos el skillset en el motor

print("✅ Servidor listo. A.L.E. está online para The Oracle Game (Modo Oráculo y Clásico).")

# --- DEFINIR LA RUTA DE EJECUCIÓN ---
# Vercel redirigirá las peticiones de /api/execute a esta función.
@app.route('/api/execute', methods=['POST'])
def handle_execution():
    datos_peticion = request.json
    try:
        # Bucle de eventos para manejar tareas asíncronas (como las de g4f)
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Procesamos la petición y obtenemos la respuesta
    respuesta_de_ale = loop.run_until_complete(ale.procesar_peticion(datos_peticion))
    
    # Devolvemos la respuesta al frontend en formato JSON
    return jsonify(respuesta_de_ale)

# --- PUNTO DE ARRANQUE (Útil para pruebas locales, Vercel lo ignora) ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
