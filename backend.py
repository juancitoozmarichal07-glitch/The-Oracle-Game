# =================================================
# == BACKEND.PY - PLAN Z (CEREBRO DE MENTIRA)    ==
# =================================================
# Este backend NO llama a la IA. Solo simula una respuesta.

from flask import Flask, request, jsonify
from flask_cors import CORS
import time # Importamos time para simular una espera

app = Flask(__name__)
CORS(app)

@app.route('/ask', methods=['POST'])
def handle_ask_fake():
    print("--- PLAN Z: Petición recibida en el Cerebro de Mentira. ---")
        
    # Simulamos que estamos "pensando" durante 3 segundos
    time.sleep(3)

    # Creamos una respuesta JSON falsa, como si la IA la hubiera generado
    fake_ia_response = [{
        "generated_text": """{
            "nombre": "Batman (Simulado)",
            "es_humano": true,
            "universo": "DC",
            "rol": "héroe",
            "habilidad_principal": "Esta es una prueba",
            "identidad_secreta": "El sistema funciona"
        }"""
    }]
        
    print("--- PLAN Z: Enviando respuesta FALSA al juego. ---")
        
    # Devolvemos la respuesta falsa al juego
    return jsonify(fake_ia_response)

# No necesitamos la línea app.run() para Render
