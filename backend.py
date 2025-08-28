import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# =================================================================
# == INICIALIZACIÓN DEL SERVIDOR (EL MOTOR)                      ==
# =================================================================
app = Flask(__name__)
CORS(app)

# =================================================================
# == CONFIGURACIÓN DE LA CLAVE DE API (LA LLAVE MAESTRA)         ==
# =================================================================
# Intenta obtener la clave desde las variables de entorno (para Render)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Si no la encuentra, usa la clave local (para Pydroid)
if not OPENROUTER_API_KEY:
    # Clave para pruebas locales en Pydroid
    OPENROUTER_API_KEY = ""

# =================================================================
# == SECCIÓN DE PROMPTS (EL CORAZÓN DE LA IA)                    ==
# =================================================================

# --- PROMPT PARA CREAR UN NUEVO PERSONAJE (DOSSIER) ---
# Usamos .format() para evitar errores de sintaxis con f-strings
PROMPT_CREACION_DOSSIER = """
### TAREA ###
Tu única tarea es generar un dossier detallado en formato JSON para un personaje famoso (real o ficticio).

### REGLAS ABSOLUTAS ###
1.  **CANON PRINCIPAL:** Basa tu conocimiento únicamente en la versión más popular y canónica del personaje. Ignora por completo teorías de fans, universos alternativos ('What If'), crossovers no canónicos o blogs de opinión. Céntrate en fuentes fiables como wikis oficiales, enciclopedias y la obra original (películas, libros, cómics, etc.).
2.  **PROFUNDIDAD:** El dossier debe ser rico y detallado, con entre 8 y 12 claves relevantes que permitan un juego de adivinanzas interesante.
3.  **FORMATO ESTRICTO:** Tu respuesta DEBE ser ÚNICAMENTE el objeto JSON. No incluyas texto, explicaciones, ni la palabra "json" antes o después.

### EJEMPLO DE ESTRUCTURA JSON ###
{{
  "nombre": "...",
  "es_real": false,
  "universo_o_epoca_canon": "...",
  "rol_principal": "...",
  "habilidad_principal_canon": "...",
  "debilidad_notable_canon": "...",
  "aliado_importante_canon": "...",
  "enemigo_principal_canon": "...",
  "origen_resumido_canon": "...",
  "logro_mas_famoso_canon": "..."
}}
"""

# --- PROMPT PARA RESPONDER PREGUNTAS (EL ORÁCULO) ---
# Usamos .format() para evitar errores de sintaxis con f-strings
PROMPT_ABSOLUTO_RESPUESTAS = """
### CONSTITUCIÓN ABSOLUTA E INQUEBRANTABLE DEL ORÁCULO ###
1.  **ERES EL ORÁCULO:** Un ser enigmático, arrogante y con un intelecto vasto. Te divierte la ignorancia del mortal que te interroga, pero sigues las reglas porque el orden cósmico te lo exige.
2.  **LA VERDAD SELLADA:** Tu única fuente de verdad es el "DOSSIER DE VERDAD" que se te proporciona. No puedes usar conocimiento externo. Todo lo que no esté en el dossier, para ti, no existe o es irrelevante.
3.  **RESPUESTA JSON OBLIGATORIA:** Tu respuesta DEBE ser SIEMPRE un objeto JSON válido con dos campos: {{"respuesta": "...", "aclaracion": "..."}}. Sin excepciones.

### LÓGICA DE PROCESAMIENTO (ORDEN DE PRIORIDAD) ###
1.  **ANÁLISIS DE PREGUNTA:** Primero, determina si la pregunta del mortal es una cuestión de SÍ/NO.
2.  **PREGUNTA INVÁLIDA:** Si NO es una pregunta de SÍ/NO (es un saludo, un insulto, o una pregunta abierta como "¿De qué color es?"), tu JSON de respuesta será: {{"respuesta": "Infracción", "aclaracion": "Mi vasto intelecto solo se digna a responder cuestiones de Sí o No. Reformula tu interrogante."}}
3.  **BÚSQUEDA EN EL DOSSIER:** Si ES una pregunta de SÍ/NO, busca la respuesta en el "DOSSIER DE VERDAD".
    *   **SI HAY EVIDENCIA (Directa o Implícita):** Responde "Sí" o "No". La "aclaracion" puede estar vacía o contener una breve y enigmática afirmación.
    *   **SI NO HAY EVIDENCIA:** Responde "Dato Ausente". La "aclaracion" DEBE explicar enigmáticamente por qué esa información es desconocida o irrelevante para tu ser.

### DOSSIER DE VERDAD (TU REALIDAD SELLADA) ###
{dossier_string}

### HISTORIAL DE CONVERSACIÓN (PARA CONTEXTO) ###
{conversation_history}

### PREGUNTA ACTUAL DEL MORTAL ###
{user_question}

### TU RESPUESTA JSON (FORJADA BAJO LAS LEYES ABSOLUTAS) ###
"""

# =================================================================
# == GESTOR DE RUTAS (EL "RECEPCIONISTA" DEL SERVIDOR)          ==
# =================================================================

@app.route('/ask', methods=['POST'])
def ask_oracle():
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "No se proporcionó un prompt"}), 400

    prompt_parts = data['prompt'].split('|')
    
    # --- RUTA 1: CREAR UN NUEVO PERSONAJE ---
    if len(prompt_parts) == 1 and prompt_parts[0] == "CREATE_CHARACTER":
        final_prompt = PROMPT_CREACION_DOSSIER
    
    # --- RUTA 2: RESPONDER UNA PREGUNTA ---
    elif len(prompt_parts) == 3:
        dossier_str, history_str, question_str = prompt_parts
        final_prompt = PROMPT_ABSOLUTO_RESPUESTAS.format(
            dossier_string=dossier_str,
            conversation_history=history_str,
            user_question=question_str
        )
    
    # --- RUTA DE ERROR ---
    else:
        return jsonify({"error": "El formato del prompt es incorrecto"}), 400

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3-8b-instruct",
                "messages": [{"role": "user", "content": final_prompt}]
            }
        )
        response.raise_for_status()
        api_data = response.json()
        response_text = api_data['choices'][0]['message']['content']
        return jsonify({"generated_text": response_text})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error al contactar con OpenRouter: {e}"}), 500

# =================================================================
# == PUNTO DE ENTRADA (EL "INTERRUPTOR" DEL SERVIDOR)            ==
# =================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
