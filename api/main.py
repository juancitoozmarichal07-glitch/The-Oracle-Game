# ===================================================================
# main.py - El Corazón del Servidor A.L.E. (v6.0 - Arquitectura Robusta)
# ===================================================================
# Esta versión es simple, correcta y delega la lógica al motor Core,
# que es exactamente como debe ser.
# ===================================================================

import sys
import os
import asyncio
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- 1. CONFIGURACIÓN DE RUTA DEL PROYECTO ---
# (Esto asume que tus skillsets están en una carpeta llamada 'skillsets')
ruta_del_proyecto = os.path.dirname(os.path.abspath(__file__))
if ruta_del_proyecto not in sys.path:
    sys.path.append(ruta_del_proyecto)
print(f"✅ Ruta del proyecto '{os.path.basename(ruta_del_proyecto)}' añadida al path.")

# --- 2. IMPORTACIÓN DE TODOS LOS COMPONENTES ---
try:
    from ale_core import ALE_Core
    from skillsets.oracle import Oracle
    from skillsets.akinator import Akinator
    # Puedes añadir aquí futuros skillsets como Analyzer, Guardian, etc.
    print("✅ Todos los componentes y skillsets importados correctamente.")
except ModuleNotFoundError as e:
    print(f"🚨 ERROR DE IMPORTACIÓN: No se pudo encontrar un componente: {e}")
    sys.exit()

# --- 3. CONFIGURACIÓN DE LA APLICACIÓN FLASK ---
app = Flask(__name__)
CORS(app) # Permite peticiones desde cualquier origen (como Vercel)

# --- 4. INICIALIZACIÓN DEL MOTOR Y CARGA DE SKILLSETS ---
print("Inicializando motor Core...")
ale = ALE_Core()

print("Cargando skillsets en el motor...")
ale.cargar_skillset("oracle", Oracle())
ale.cargar_skillset("akinator", Akinator())
print("✅ Servidor listo. El Sistema A.L.E. está online.")

# --- 5. RUTA ÚNICA Y EFICIENTE DE LA API ---
@app.route('/api/execute', methods=['POST'])
def handle_execution():
    """
    Maneja TODAS las peticiones de ejecución desde el frontend.
    El motor ALE_Core se encarga de dirigir la petición al skillset correcto.
    """
    datos_peticion = request.json
    print(f"-> Petición API recibida para el skillset: '{datos_peticion.get('skillset_target')}'")
    
    try:
        # La forma correcta y simple: le pasamos la petición al motor
        # y él se encarga de todo lo demás.
        respuesta = asyncio.run(ale.procesar_peticion(datos_peticion))
        return jsonify(respuesta)
    except Exception as e:
        print(f"🚨 ERROR CRÍTICO en handle_execution: {e}")
        traceback.print_exc() # Imprime el error completo para un mejor diagnóstico
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

# --- 6. ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    print("-" * 40)
    print(f"🚀 Iniciando servidor Flask en http://0.0.0.0:5000")
    print("   El endpoint de la API es /api/execute")
    print("-" * 40)
    # El debug=False es importante para producción en Replit.
    app.run(host='0.0.0.0', port=5000, debug=False)

