# =================================================================
# == MAIN.PY - EDICIÓN "GUARDIAN & AKINATOR" PARA VERCEL         ==
# =================================================================
# - Esta versión solo importa y carga los skillsets Guardian y
#   Akinator, ideal para un despliegue enfocado.

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
sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Sube un nivel
sys.path.append(os.path.dirname(os.path.abspath(__file__)))   # Se mantiene por si acaso

# --- IMPORTAR E INICIALIZAR EL CEREBRO (SOLO GUARDIAN Y AKINATOR) ---
from ale_core import ALE_Core
from skillsets.guardian import Guardian
from skillsets.akinator import Akinator

# 1. Creamos la instancia del motor A.L.E.
ale = ALE_Core()

# 2. Cargamos ÚNICAMENTE los skillsets necesarios.
print("Cargando skillsets en el motor A.L.E...")
ale.cargar_skillset("guardian", Guardian())
ale.cargar_skillset("akinator", Akinator())

print("✅ Servidor listo. A.L.E. está online con los skillsets Guardian y Akinator.")

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

# --- PUNTO DE ARRANQUE (Vercel lo ignora, pero es útil para pruebas locales) ---
if __name__ == "__main__":
    # En Vercel, esta parte no se ejecuta. Vercel usa un servidor WSGI.
    app.run(host='0.0.0.0', port=5000, debug=True)
