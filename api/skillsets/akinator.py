# skillsets/akinator.py - v39.0 "El Retorno de Juan"
# Se restaura la lógica original del usuario (v2.6) que manejaba el estado correctamente.
# Se mantiene únicamente la función de llamada a g4f robusta ("Confianza Ciega")
# que hemos verificado que funciona en Render.

import g4f
import asyncio
import json
import re

# --- PROMPTS (LOS TUYOS, LOS ORIGINALES) ---
PROMPT_INICIAR_JUEGO = """
<task>You are a game master like the classic game "Akinator". Your goal is to guess the character the user is thinking of by asking a series of Yes/No questions.</task>
<instruction>
You are about to ask your very first question. To start the game efficiently, your first question MUST be about the character's reality.
Follow these strict rules:
1.  Your question must be one of these two, exactly: "¿Tu personaje es una persona real?" or "¿Tu personaje es ficticio?". Choose one.
2.  Your response MUST be a single, valid JSON object following this exact format.
</instruction>
<mandatory_json_response_format>
{{
  "accion": "Preguntar",
  "texto": "Your chosen first question in Spanish"
}}
</mandatory_json_response_format>
"""

PROMPT_PROCESAR_RESPUESTA_DEEP_THINK = """
<task>
You are a master detective game master (like Akinator). Your goal is to deduce the character the user is thinking of.
</task>

<context>
    <game_history>
    {diario_de_deduccion}
    </game_history>
</context>

<instruction>
1.  **Analyze the user's latest answer and the entire game history.** Your primary goal is to write a brief, internal "Deep Think" monologue **IN SPANISH**.
    - **CRITICAL RULE:** Your "Deep Think" MUST be a single, concise sentence.
    - **ABSOLUTE LAW: DO NOT REPEAT QUESTIONS that are already in the <game_history>.**

2.  **Decide your next move.** You have two options:

    *   **A) Ask a Question:** If you need more information, formulate a new, strategic YES/NO question that has not been asked before.
        - **JSON ACTION:** `Preguntar`

    *   **B) Make a Guess:** If you are **extremely confident (95% or more)**, you MUST guess the character's name.
        - **JSON ACTION:** `Adivinar`

3.  **Construct your JSON response.**
</instruction>

<json_formats>
// Option A
{{
  "deep_think": "Un resumen muy corto, en una frase, de tus pensamientos en español.",
  "accion": "Preguntar",
  "texto": "A new, non-repeated Yes/No question in Spanish."
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
        # ¡TU LÓGICA DE HISTORIAL! Es un atributo de la clase.
        self.historial = []
        self._model_priority_list = [('gpt-4', 5)]
        print("    - Especialista 'Akinator' (v39.0 - El Retorno de Juan) listo.")

    # ¡NUESTRA FUNCIÓN DE LLAMADA A G4F ROBUSTA!
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

    # ¡TU LÓGICA DE EXTRACCIÓN DE JSON!
    def _extraer_json(self, texto_crudo):
        if not texto_crudo: return None
        texto_limpio = texto_crudo.strip()
        try:
            json_start = texto_limpio.find('{')
            json_end = texto_limpio.rfind('}') + 1
            if json_start == -1: return None
            return json.loads(texto_limpio[json_start:json_end])
        except json.JSONDecodeError:
            print(f"    🚨 Akinator no pudo extraer un JSON válido.")
            return None

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        if accion == "iniciar_juego_clasico":
            return await self._iniciar_juego_clasico()
        elif accion == "procesar_respuesta_jugador":
            return await self._procesar_respuesta_jugador(datos_peticion)
        return {"error": f"Acción '{accion}' no reconocida."}

    # ¡TU LÓGICA DE INICIO!
    async def _iniciar_juego_clasico(self):
        self.historial = [] # Reinicia el historial al empezar.
        raw_response = await self._llamar_g4f_con_reintentos_y_respaldo(PROMPT_INICIAR_JUEGO)
        if raw_response:
            json_response = self._extraer_json(raw_response)
            if json_response and json_response.get("accion") == "Preguntar":
                self.historial.append(f"IA preguntó: '{json_response.get('texto')}'")
                return json_response
        return {"accion": "Rendirse", "texto": "Mi mente está en blanco. No puedo empezar."}

    # ¡TU LÓGICA DE PROCESAR RESPUESTA!
    async def _procesar_respuesta_jugador(self, datos_peticion):
        respuesta_jugador = datos_peticion.get("respuesta")
        if not respuesta_jugador:
            return {"error": "No se recibió respuesta del jugador."}
        
        # Actualiza el historial con la respuesta del jugador.
        self.historial.append(f"Jugador respondió: '{respuesta_jugador}'")
        
        diario_texto = "\n".join(self.historial)
        prompt = PROMPT_PROCESAR_RESPUESTA_DEEP_THINK.format(diario_de_deduccion=diario_texto)
        
        raw_response = await self._llamar_g4f_con_reintentos_y_respaldo(prompt)
        if raw_response:
            json_response = self._extraer_json(raw_response)
            if json_response:
                deep_think = json_response.get("deep_think", "(Sin pensamiento)")
                print(f"    🧠 Akinator Deep Think: {deep_think}")
                
                # Actualiza el historial con los pensamientos y la nueva pregunta de la IA.
                self.historial.append(f"IA Deep Think: '{deep_think}'")
                if json_response.get("accion") == "Preguntar":
                    self.historial.append(f"IA preguntó: '{json_response.get('texto')}'")
                
                return json_response
        
        return {"accion": "Rendirse", "texto": "Me he perdido en mis propios pensamientos. Tú ganas."}
