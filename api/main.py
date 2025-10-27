# ===================================================================
# main.py - El Corazón del Servidor (v5.3 - Arquitectura Completa)
# ===================================================================
# Esta es la versión completa del servidor.
# Carga TODOS los skillsets existentes y añade Guardian 2.0.
# ===================================================================

import sys
import os
import asyncio
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# --- 1. CONFIGURACIÓN DE RUTA DEL PROYECTO ---
ruta_del_proyecto = os.path.dirname(os.path.abspath(__file__))
if ruta_del_proyecto not in sys.path:
    sys.path.append(ruta_del_proyecto)
print(f"✅ Ruta del proyecto '{os.path.basename(ruta_del_proyecto)}' añadida al path.")

# --- 2. IMPORTACIÓN DE TODOS LOS COMPONENTES ---
# Se importan el motor y todos los skillsets que forman tu sistema.
try:
    from ale_core import ALE_Core
    from skillsets.guardian_skillset import GuardianSkillset # <-- Nuestro Guardian 2.0
    from skillsets.oracle import Oracle
    from skillsets.akinator import Akinator
    from skillsets.analyzer import Analyzer
    print("✅ Todos los componentes y skillsets importados correctamente.")
except ModuleNotFoundError as e:
    print(f"🚨 ERROR DE IMPORTACIÓN: No se pudo encontrar un componente: {e}")
    print("   Asegúrate de que todos los archivos de skillsets (oracle.py, veridian.py, etc.) existen en la carpeta 'skillsets'.")
    sys.exit()

# --- 3. CONFIGURACIÓN DE LA APLICACIÓN FLASK ---
app = Flask(__name__, template_folder='templates')
CORS(app)

# --- 4. INICIALIZACIÓN DEL MOTOR Y CARGA DE TODOS LOS SKILLSETS ---
print("Inicializando motor Core...")
ale = ALE_Core()

print("Cargando todos los skillsets en el motor...")
# Se cargan los skillsets originales
ale.cargar_skillset("oracle", Oracle())
ale.cargar_skillset("akinator", Akinator())
ale.cargar_skillset("analyzer", Analyzer())
# Se carga nuestro nuevo Guardian 2.0 con el nombre clave "guardian"
ale.cargar_skillset("guardian", GuardianSkillset())
print("✅ Servidor listo. El Sistema está online con todos los skillsets cargados.")

# --- 5. RUTAS DE LA APLICACIÓN (URLs) ---
@app.route('/')
def index():
    """Sirve la interfaz de chat principal."""
    print("-> Petición recibida para la interfaz de chat. Sirviendo index.html...")
    return render_template('index.html')

@app.route('/api/execute', methods=['POST'])
def handle_execution():
    """Maneja las peticiones de ejecución desde el frontend."""
    datos_peticion = request.json
    print(f"-> Petición API recibida para el skillset: '{datos_peticion.get('skillset_target')}'")
    
    try:
        respuesta = asyncio.run(ale.procesar_peticion(datos_peticion))
        return jsonify(respuesta)
    except Exception as e:
        print(f"🚨 ERROR INESPERADO DURANTE LA EJECUCIÓN: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

# --- 6. ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    print("-" * 40)
    print(f"🚀 Iniciando servidor Flask en http://0.0.0.0:5000")
    print("   Abre tu navegador y ve a http://localhost:5000 para usar el chat.")
    print("-" * 40)
    app.run(host='0.0.0.0', port=5000, debug=False)
()
