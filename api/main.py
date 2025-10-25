# main.py - El Corazón del Servidor v6.0 (El Guardián de la Puerta)
# MEJORAS:
# - Añadida ruta de "ping" para UptimeRobot en '/'.
# - Mejorado el manejo de errores para peticiones inválidas.
# - Añadida validación básica de datos de entrada.
# - Código más limpio y comentado.

import sys
import os
import asyncio
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# --- 1. CONFIGURACIÓN DE RUTA DEL PROYECTO ---
# (Sin cambios, sigue siendo perfecto)
try:
    ruta_del_proyecto = os.path.dirname(os.path.abspath(__file__))
    if ruta_del_proyecto not in sys.path:
        sys.path.append(ruta_del_proyecto)
    print("✅ Ruta del proyecto añadida al path.")
except NameError:
    print("⚠️ No se pudo determinar la ruta del proyecto. Asumiendo que está en el path.")
    pass

# --- 2. IMPORTACIÓN DE TODOS LOS COMPONENTES ---
# (Sin cambios)
try:
    from ale_core import ALE_Core
    from skillsets.guardian_skillset import GuardianSkillset
    from skillsets.oracle import Oracle
    from skillsets.akinator import Akinator
    from skillsets.analyzer import Analyzer
    print("✅ Todos los componentes y skillsets importados correctamente.")
except ImportError as e:
    print(f"🚨 ERROR DE IMPORTACIÓN: {e}. Asegúrate de que todos los archivos de skillsets existen.")
    sys.exit(1)

# --- 3. CONFIGURACIÓN DE LA APLICACIÓN FLASK ---
app = Flask(__name__, template_folder='templates')
CORS(app) # Permite peticiones desde tu PWA en Vercel

# --- 4. INICIALIZACIÓN DEL MOTOR Y CARGA DE SKILLSETS ---
print("🚀 Inicializando Sistema A.L.E. v6.0...")
ale = ALE_Core()

# Cargamos todos los "cerebros"
ale.cargar_skillset("oracle", Oracle())
ale.cargar_skillset("akinator", Akinator())
ale.cargar_skillset("analyzer", Analyzer())
ale.cargar_skillset("guardian", GuardianSkillset())
print("✅ Sistema A.L.E. online con todos los skillsets cargados.")

# --- 5. RUTAS DE LA APLICACIÓN (URLs) ---

# ¡NUEVO! Ruta de "ping" para UptimeRobot y curiosos.
@app.route('/')
def health_check():
    """
    Responde a las peticiones 'ping' para mantener el servidor despierto
    y confirma que el servicio está online.
    """
    return "Servidor A.L.E. v6.0 Online", 200

# Ruta para la interfaz de chat de prueba (si la necesitas)
@app.route('/chat')
def index():
    """Sirve la interfaz de chat de prueba."""
    return render_template('index.html')

# ¡MEJORADO! Ruta principal de la API.
@app.route('/api/execute', methods=['POST'])
def handle_execution():
    """Maneja las peticiones de ejecución desde el frontend."""
    
    # Validación 1: ¿La petición tiene un cuerpo JSON?
    if not request.is_json:
        return jsonify({"error": "Petición inválida: se esperaba un cuerpo JSON."}), 400
        
    datos_peticion = request.json
    
    # Validación 2: ¿La petición especifica un 'skillset_target'?
    skillset_target = datos_peticion.get("skillset_target")
    if not skillset_target:
        return jsonify({"error": "Petición inválida: 'skillset_target' es requerido."}), 400

    print(f"-> Petición API recibida para el skillset: '{skillset_target}'")
    
    try:
        # Usamos asyncio.run() que es la forma moderna y recomendada.
        respuesta = asyncio.run(ale.procesar_peticion(datos_peticion))
        return jsonify(respuesta)
    except Exception as e:
        print(f"🚨 ERROR CRÍTICO DURANTE LA EJECUCIÓN: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

# --- 6. ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    print("-" * 50)
    print(f"🚀 Iniciando servidor Flask en http://0.0.0.0:5000")
    print("   -> Ruta de API: /api/execute (POST)")
    print("   -> Ruta de Salud: / (GET)")
    print("-" * 50)
    # Usamos Gunicorn o un servidor de producción en un entorno real,
    # pero para Replit, esto es suficiente.
    app.run(host='0.0.0.0', port=5000, debug=False)

