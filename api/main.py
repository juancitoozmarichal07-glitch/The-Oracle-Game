# main.py - El Corazón del Servidor v7.0 (El Guardián Despierto)
# MEJORAS:
# - Añadido despertador interno para el servidor cooperativo.

import sys
import os
import asyncio
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import threading
import requests # ¡Importante!

# --- CONFIGURACIÓN ---
try:
    # (El resto de tus imports y configuración inicial se mantiene igual)
    # ...
    from ale_core import ALE_Core
    from skillsets.oracle import Oracle
    from skillsets.akinator import Akinator
    # ...
except ImportError as e:
    print(f"🚨 ERROR DE IMPORTACIÓN: {e}.")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# ¡IMPORTANTE! La URL de tu otro servidor, el cooperativo
COOP_SERVER_URL = "https://ff849e56-b6b6-4619-8495-996867c9bc5c-00-1rg9nfq7thllg.picard.replit.dev/"

print("🚀 Inicializando Sistema A.L.E. v7.0 (con Despertador Interno)...")

ale = ALE_Core()
ale.cargar_skillset("oracle", Oracle())
ale.cargar_skillset("akinator", Akinator())
# (Carga tus otros skillsets aquí si los tienes)
print("✅ Sistema A.L.E. online con todos los skillsets cargados.")


# --- FUNCIÓN DESPERTADOR ---
def ping_coop_server():
    """Cada 4 minutos, hace una petición al servidor cooperativo para mantenerlo despierto."""
    while True:
        print("⏰ [Despertador] Haciendo ping al servidor cooperativo...")
        try:
            requests.get(COOP_SERVER_URL, timeout=10)
            print("✅ [Despertador] Ping al servidor cooperativo exitoso.")
        except requests.RequestException as e:
            print(f"🚨 [Despertador] Error en el ping al servidor cooperativo: {e}")
        time.sleep(240) # Espera 4 minutos

# --- RUTAS ---
@app.route('/')
def health_check():
    return "Servidor A.L.E. v7.0 Online", 200

@app.route('/api/execute', methods=['POST'])
def handle_execution():
    # (Tu función handle_execution se mantiene exactamente igual)
    if not request.is_json:
        return jsonify({"error": "Petición inválida: se esperaba un cuerpo JSON."}), 400
    datos_peticion = request.json
    skillset_target = datos_peticion.get("skillset_target")
    if not skillset_target:
        return jsonify({"error": "Petición inválida: 'skillset_target' es requerido."}), 400
    print(f"-> Petición API recibida para el skillset: '{skillset_target}'")
    try:
        respuesta = asyncio.run(ale.procesar_peticion(datos_peticion))
        return jsonify(respuesta)
    except Exception as e:
        print(f"🚨 ERROR CRÍTICO DURANTE LA EJECUCIÓN: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

# --- ARRANQUE ---
if __name__ == "__main__":
    # Inicia el despertador en un hilo separado
    threading.Thread(target=ping_coop_server, daemon=True).start()
    # Inicia el servidor del juego
    app.run(host='0.0.0.0', port=5000, debug=False)
