# =======================================================
# == BACKEND.PY - VERSIÓN FINAL (CONECTADO A OPENROUTER) ==
# =======================================================
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests # Volvemos a usar requests, es más simple para esto

app = Flask(__name__)
CORS(app)

# Leemos la clave maestra de las variables de entorno de Render
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

@app.route('/ask', methods=['POST'])
def handle_ask():
    print("--- Petición recibida en el Cerebro (versión OpenRouter) ---")
        
    if not OPENROUTER_API_KEY:
        return jsonify({"error": "La clave de API de OpenRouter no está configurada."}), 500

    if not request.json or 'prompt' not in request.json:
        return jsonify({"error": "Petición mal formada."}), 400

    prompt = request.json['prompt']
    print("--- Enviando prompt a la API de OpenRouter... ---")

    try:
        # Hacemos la llamada a la API de OpenRouter
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3-8b-instruct", # ¡Podemos usar Llama 3 a través de OpenRouter!
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )
            
        response.raise_for_status() # Captura errores como 4xx o 5xx
            
        data = response.json()
            
        # Extraemos la respuesta
        response_text = data['choices'][0]['message']['content']
            
        # Envolvemos la respuesta en el formato que espera nuestro frontend
        final_response = [{"generated_text": response_text}]
            
        print("--- ¡ÉXITO! Respuesta recibida de OpenRouter. ---")
        return jsonify(final_response)

    except requests.exceptions.RequestException as e:
        error_message = f"Error al contactar con la API de OpenRouter: {e}"
        if e.response is not None:
            error_message += f" | Respuesta del servidor: {e.response.text}"
            
        print(f"¡¡¡FALLO CRÍTICO!!! {error_message}")
        return jsonify({"error": error_message}), 500
