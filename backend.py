# =================================================
# == BACKEND.PY - VERSIÓN FINAL PARA RENDER      ==
# =================================================
# Hecho por Manus para ti. ¡A disfrutar!

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os # Importamos 'os' para poder leer la clave de API desde Render

# --- CONFIGURACIÓN ---

# Render nos dará la clave de API a través de una "variable de entorno".
# Si no la encuentra, usará la que pongamos aquí (para pruebas locales).
HF_API_KEY = os.environ.get("HUGGING_FACE_API_KEY", "pon_aqui_tu_clave_hf_si_quieres_probar_en_local")

# Usaremos el modelo Llama-3 8B, que es potente y estable.
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
# --- FIN DE LA CONFIGURACIÓN ---


# Creamos la aplicación Flask
app = Flask(__name__)

# Configuramos CORS para permitir que nuestro juego (desde cualquier dirección) hable con este cerebro.
CORS(app)


# Esta es la única "puerta" de nuestro cerebro. Se activa cuando el juego llama a "/ask"
@app.route('/ask', methods=['POST'])
def handle_ask():
    """
    Recibe un prompt del juego, se lo pasa a la IA de Hugging Face,
    y devuelve la respuesta de la IA al juego.
    """
    print("--- PASO 1: Petición recibida en el Cerebro (backend.py) ---")

    # Verificamos que nos han enviado datos correctos
    if not request.json or 'prompt' not in request.json:
        print("--- ERROR: La petición no contenía un prompt en formato JSON. ---")
        return jsonify({"error": "Petición mal formada. Se esperaba un 'prompt'."}), 400

    prompt = request.json['prompt']
    print(f"--- PASO 2: Recibido prompt del juego. Primeras 80 letras: '{prompt[:80]}...' ---")

    # Preparamos la llamada a la API de Hugging Face
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 250, # Aumentamos un poco por si el dossier es largo
            "return_full_text": False # ¡Importante! Para que no repita el prompt
        }
    }

    print("--- PASO 3: Enviando petición a la IA de Hugging Face... (puede tardar) ---")
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
        
        # Si la API de HF devuelve un error (4xx o 5xx), esta línea lo capturará
        response.raise_for_status() 
        
        data = response.json()
        print("--- PASO 4: ¡ÉXITO! Respuesta recibida de la IA. ---")
        
        # Devolvemos la respuesta de la IA al juego
        return jsonify(data)

    except requests.exceptions.RequestException as e:
        # Este error ocurre si hay un problema de conexión, timeout, o un error de la API
        print("\n¡¡¡FALLO CRÍTICO EN LA COMUNICACIÓN CON LA IA!!!")
        error_message = f"Error al contactar con la API de Hugging Face: {e}"
        if e.response is not None:
            error_message += f" | Respuesta del servidor: {e.response.text}"
        
        print(error_message)
        
        # Devolvemos un mensaje de error claro al juego
        return jsonify({"error": "Error en la comunicación con la IA"}), 500

# --- NO AÑADAS LA LÍNEA app.run() AQUÍ ---
# Render se encarga de ejecutar la aplicación con Gunicorn,
# por lo que no necesitamos el app.run() que usábamos en Pydroid.
