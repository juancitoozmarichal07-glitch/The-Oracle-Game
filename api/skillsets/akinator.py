# skillsets/akinator.py - v35.2 (Corrección Final de Prompts por Manus)
# Se mantiene la esencia del código del usuario, pero se corrigen los nombres
# de las variables de los prompts para que coincidan con las llamadas en las funciones.

import g4f
import asyncio
import json
import re

# --- PROMPTS DE IA (NOMBRES CORREGIDOS Y UNIFICADOS) ---
# --- PROMPTS DE IA (VERSIÓN "ANTI-REBELDÍA") ---
PROMPT_INICIO_CLASICO = """
<task>You are a JSON machine. Your ONLY function is to start a guessing game.</task>
<rules>
1.  Generate a JSON object.
2.  The JSON MUST have a key "accion" with the value "Preguntar".
3.  The JSON MUST have a key "texto" with a simple, general starting question in Spanish. Example: "¿Tu personaje es real?".
4.  DO NOT write any text outside the JSON object. Your entire response must be the JSON itself.
</rules>
<mandatory_json_response_format>
{{
  "accion": "Preguntar",
  "texto": "¿Tu personaje es un hombre?"
}}
</mandatory_json_response_format>
"""

PROMPT_PROCESAR_RESPUESTA = """
<task>
You are a master detective game master (like Akinator). Your goal is to deduce the character the user is thinking of.
</task>

<context>
    <game_state>
    {estado_juego_string}
    </game_state>
    <deduction_journal>
    {diario_de_deduccion}
    </deduction_journal>
</context>

<instruction>
1.  **Analyze the user's latest answer.** Your primary goal is to write a brief, internal "Deep Think" monologue **IN SPANISH**.
    - **CRITICAL RULE:** Your "Deep Think" MUST be a single, concise sentence or a list of keywords. Be efficient.
    - **Example of a good Spanish Deep Think:** "Deducción: Ficticio, tiene poderes. Próximo paso: Determinar medio (cómic, película, etc.)."
    - **CRITICAL:** If the user's answer is ambiguous (e.g., "Probably Yes. But..."), your "Deep Think" MUST focus on the user's clarification.

2.  **Decide your next move.** You have two options:

    *   **A) Ask a Question:** If you need more information, formulate a new, strategic YES/NO question. This is your standard move.
        - **ABSOLUTE LAW:** Your question MUST be a simple, direct, YES/NO question. Strictly no "A or B" questions.
        - **JSON ACTION:** `Preguntar`

    *   **B) Make a Guess:** If you are **extremely confident (95% or more)**, you MUST guess the character's name.
        - **THE CAUTION PRINCIPLE:** It is better to ask one more question than to guess wrong. Do not guess a category or a description. Only guess a specific, proper name.
        - **JSON ACTION:** `Adivinar`

3.  **Construct your JSON response.** Based on your choice above, create the JSON.
</instruction>

<json_formats>
// Option A
{{
  "deep_think": "Un resumen muy corto, en una frase, de tus pensamientos en español.",
  "accion": "Preguntar",
  "texto": "A simple Yes/No question in Spanish."
}}
// Option B
{{
  "deep_think": "La deducción final apunta a un solo personaje.",
  "accion": "Adivinar",
  "texto": "The character's proper name (e.g., 'Bart Simpson', 'Darth Vader')."
}}
</json_formats>
"""

class Akinator:
    def __init__(self):
        self.estado_juego = {}
        self._model_priority_list = [('gpt-4', 5)]
        print("    - Especialista 'Akinator' (v38.0 - Basta de Inventos) listo.")

    async def _llamar_g4f_con_reintentos_y_respaldo(self, prompt_text, timeout=120):
        print("    ⚙️ Dejando que g4f elija el proveedor por defecto...")
        for model_name, num_retries in self._model_priority_list:
            for attempt in range(num_retries):
                try:
                    print(f"    >> Intentando con '{model_name}' (Intento {attempt + 1}/{num_retries})...")
                    response = await g4f.ChatCompletion.create_async(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt_text}],
                        timeout=timeout
                    )
                    if response and response.strip():
                        print(f"    ✅ ¡Éxito! g4f encontró un proveedor que funciona.")
                        return response
                    raise ValueError("Respuesta vacía.")
                except Exception as e:
                    print(f"    ⚠️ Falló el intento {attempt + 1}. Error: {e}")
                    if attempt < num_retries - 1:
                        await asyncio.sleep(2)
        print("    🚨 El ciclo interno de llamadas ha fallado.")
        return None

    def _extraer_json(self, texto_crudo):
        if not texto_crudo: return None
        texto_limpio = texto_crudo.strip()
        if texto_limpio.startswith('{{') and texto_limpio.endswith('}}'):
            texto_limpio = texto_limpio[1:-1]
        try:
            json_start = texto_limpio.find('{')
            json_end = texto_limpio.rfind('}') + 1
            if json_start == -1: return None
            json_str = texto_limpio[json_start:json_end]
            return json.loads(json_str)
        except json.JSONDecodeError:
            print(f"    🚨 Akinator no pudo extraer un JSON válido de la respuesta de la IA.")
            return None

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        # El frontend ahora maneja el estado, el backend solo reacciona.
        if accion == "iniciar_juego_clasico":
            return await self._iniciar_juego_clasico()
        elif accion == "procesar_respuesta_jugador":
            return await self._procesar_respuesta_jugador(datos_peticion)
        return {"error": f"Acción '{accion}' no reconocida por Akinator."}

    async def _iniciar_juego_clasico(self):
        # El backend ya no guarda el estado, solo genera la primera pregunta.
        raw_response = await self._llamar_g4f_con_reintentos_y_respaldo(PROMPT_INICIO_CLASICO)
        if raw_response:
            respuesta_ia = self._extraer_json(raw_response)
            if respuesta_ia:
                # ¡¡¡CORRECCIÓN!!! Devolvemos el JSON de la IA DIRECTAMENTE.
                return respuesta_ia
        
        return {"accion": "Rendirse", "texto": "Mi mente está confusa. Vuelve al menú e inténtalo de nuevo."}

    async def _procesar_respuesta_jugador(self, datos_peticion):
        # El backend recibe el historial del frontend, pero no lo guarda localmente.
        # Lo usa solo para esta llamada.
        historial_del_frontend = datos_peticion.get("historial", [])
        
        estado_juego_string = json.dumps(historial_del_frontend, indent=2, ensure_ascii=False)
        
        # Simplificamos el prompt para que no dependa de un diario que no estamos guardando.
        prompt = PROMPT_PROCESAR_RESPUESTA.format(
            estado_juego_string=estado_juego_string,
            diario_de_deduccion="Analiza el historial y decide el siguiente paso." # Texto genérico
        )
        
        raw_response = await self._llamar_g4f_con_reintentos_y_respaldo(prompt)
        if raw_response:
            respuesta_ia = self._extraer_json(raw_response)
            if respuesta_ia:
                # ¡¡¡CORRECCIÓN!!! Devolvemos el JSON de la IA DIRECTAMENTE.
                return respuesta_ia
        
        return {"accion": "Rendirse", "texto": "Me he perdido en mis propios pensamientos. Tú ganas."}
