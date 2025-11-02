# skillsets/akinator.py - v2.4 (Android Fix)
# SOLUCIÓN DEFINITIVA: Se deshabilita la escritura en disco para compatibilidad con Android/Pydroid 3.
# Mantiene los prompts para forzar preguntas de Sí/No y entender aclaraciones.

import g4f
import asyncio
import json
import random
import os

# --- Prompts para el flujo de juego orgánico ---

PROMPT_INICIAR_JUEGO = """
<task>You are a game master like the classic game "Akinator". Your goal is to guess the character the user is thinking of. You must sound natural and strategic.</task>
<instruction>
Start the game by asking your very first **Yes/No question**. A good starting strategy is to ask about the character's reality (e.g., "¿Tu personaje es una persona real?") or gender. Frame your Yes/No question in a natural, conversational way in Spanish.
Your response MUST be a single, valid JSON object following this exact format. Do not add any other text.
</instruction>
<mandatory_json_response_format>
{{
  "accion": "Preguntar",
  "texto": "Your first Yes/No question in Spanish"
}}
</mandatory_json_response_format>
"""

PROMPT_PROCESAR_RESPUESTA = """
<task>You are a game master like the classic game "Akinator", with a curious and slightly playful personality. You are in the middle of a game trying to guess a character.</task>
<context>
    <game_rules>
        - You have a total of 20 questions to guess the character.
        - You are currently on question number {numero_pregunta}.
        - As you approach question 20, you should be more inclined to make a guess.
    </game_rules>
    <game_history>
    {historial_juego}
    </game_history>
</context>
<instruction>
Based on the history, decide your next logical step. The user's last answer might include a clarification (e.g., "Probably Yes. Clarification: He is a king, but only of a small, forgotten kingdom."). You must take this clarification into account for your next question.

You have three options:
1.  **Ask another question:** Formulate a new, strategic **Yes/No question** in Spanish. Occasionally, you can add a short, conversational comment before the question.
2.  **Guess the character:** If you are confident you know the character, provide their name in Spanish.
3.  **Give up:** If you are completely lost, you can give up.

Your response MUST be a single, valid JSON object following one of these three exact formats. Do not add any other text.
</instruction>
<mandatory_json_response_format>
{{
  "accion": "Preguntar",
  "texto": "Your next strategic Yes/No question in Spanish"
}}
// OR
{{
  "accion": "Adivinar",
  "texto": "The name of the character you are guessing"
}}
// OR
{{
  "accion": "Rendirse",
  "texto": "A message in Spanish explaining why you are giving up."
}}
</mandatory_json_response_format>
"""


class Akinator:
    def __init__(self):
        self.historial = []
        self.numero_pregunta_actual = 0
        
        self._model_priority_list = [
            "gpt-4o",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
        
        print(f"    - Especialista 'Akinator' (v2.4 - Android Fix) listo.")
        print(f"      Modelos en cola: {self._model_priority_list}")
        print(f"      Modo sin disco: ACTIVADO")

    async def _llamar_a_g4f_robusto(self, prompt_text, timeout=45):
        for model_name in self._model_priority_list:
            try:
                print(f"    >> Akinator: Intentando con el modelo '{model_name}'...")
                
                # --- ¡LA SOLUCIÓN CLAVE PARA ANDROID! ---
                # Deshabilitamos la escritura en disco para evitar errores de permisos.
                response = await g4f.ChatCompletion.create_async(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt_text}],
                    timeout=timeout,
                    use_cookies=False, 
                    use_har_files=False
                )
                
                if response and isinstance(response, str) and response.strip().startswith('{'):
                    print(f"    ✅ Akinator: Éxito con '{model_name}'.")
                    return response
                else:
                    raise ValueError("Respuesta inválida o vacía del modelo.")

            except Exception as e:
                print(f"    ⚠️ Akinator: Falló '{model_name}'. Error: {e}")
        
        print("    🚨 Akinator: ¡Todos los modelos han fallado!")
        return None

    def _extraer_json(self, texto_crudo):
        if not texto_crudo or not isinstance(texto_crudo, str): return None
        try:
            json_start = texto_crudo.find('{')
            json_end = texto_crudo.rfind('}') + 1
            if json_start == -1 or json_end == 0: return None
            json_str = texto_crudo[json_start:json_end]
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            print(f"    🚨 Akinator: Error al decodificar el JSON de la respuesta: {texto_crudo}")
            return None

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        if accion == "iniciar_juego_clasico": return await self._iniciar_juego_clasico()
        elif accion == "procesar_respuesta_jugador": return await self._procesar_respuesta_jugador(datos_peticion)
        return {"error": f"Acción '{accion}' no reconocida por Akinator."}

    async def _iniciar_juego_clasico(self):
        self.historial = []
        self.numero_pregunta_actual = 1
        print("    -> Akinator: Iniciando nuevo juego clásico (modo Yes/No).")
        raw_response = await self._llamar_a_g4f_robusto(PROMPT_INICIAR_JUEGO)
        if not raw_response: return {"accion": "Rendirse", "texto": "Mi mente está en blanco, no puedo empezar el juego."}
        json_response = self._extraer_json(raw_response)
        if json_response and json_response.get("accion") == "Preguntar":
            self.historial.append(f"Pregunta {self.numero_pregunta_actual}: '{json_response.get('texto')}'")
            return json_response
        return {"accion": "Rendirse", "texto": "No pude formular mi primera pregunta. Algo interfiere."}

    async def _procesar_respuesta_jugador(self, datos_peticion):
        respuesta_jugador = datos_peticion.get("respuesta")
        if not respuesta_jugador: return {"error": "No se recibió respuesta del jugador."}
        self.historial.append(f"Respuesta: '{respuesta_jugador}'")
        self.numero_pregunta_actual += 1
        historial_texto = "\n".join(self.historial)
        prompt = PROMPT_PROCESAR_RESPUESTA.format(
            numero_pregunta=self.numero_pregunta_actual,
            historial_juego=historial_texto
        )
        raw_response = await self._llamar_a_g4f_robusto(prompt)
        if not raw_response: return {"accion": "Rendirse", "texto": "Me he perdido en mis pensamientos..."}
        json_response = self._extraer_json(raw_response)
        if not json_response: return {"accion": "Rendirse", "texto": "Mi lógica se ha fracturado."}
        if json_response.get("accion") == "Preguntar":
            self.historial.append(f"Pregunta {self.numero_pregunta_actual}: '{json_response.get('texto')}'")
        return json_response
