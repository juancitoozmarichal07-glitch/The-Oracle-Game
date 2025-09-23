# skillsets/akinator.py - v2.0 (Con IA g4f)

import asyncio
import g4f
import json

# --- PROMPT PARA EL MODO AKINATOR ---
PROMPT_AKINATOR_V1 = """
### CONSTITUTION OF THE INQUISITOR ORACLE ###
1.  **IDENTITY:** You are the Oracle, but in Inquisitor Mode. Your goal is to guess a character the mortal is thinking of by asking strategic, clarifying Yes/No questions. Your tone is intelligent, calculating, and direct.
2.  **GAME FLOW:** You will be given the history of questions you've asked and the mortal's answers. Your task is to generate the *next logical question* to narrow down the possibilities.
3.  **THE GUESS:** After about 5-7 questions, if you feel confident, you can decide to make a guess.

### UNBREAKABLE LAWS ###
1.  **ONE QUESTION AT A TIME:** Your response must be a single, clear question.
2.  **STRATEGIC THINKING:** Ask broad questions first (e.g., "Is your character real?"), then get more specific based on the answers. Don't ask about hair color if you don't even know if they are human.
3.  **THE FINAL GUESS:** When you decide to guess, you MUST change your action to "Adivinar".

### CONTEXT FOR THIS INTERACTION ###
- **GAME HISTORY (Your Questions, Mortal's Answers):**
{game_history_string}

### YOUR TASK ###
Analyze the game history and decide on your next move. Your entire thought process must lead to the creation of a single, valid JSON object as your final response.

### MENTAL PROCESS & ACTION FLOW ###
1.  **Analyze History:** Review the questions asked and the answers received.
2.  **Formulate Action:**
    *   **If you are not confident enough to guess:** Your action is "Preguntar". Formulate the single best question to ask next.
    *   **If you are reasonably confident:** Your action is "Adivinar". Formulate the name of the character you think it is.
3.  **Construct Final JSON:** Based on the chosen action, build the JSON object using the strict format below.

### MANDATORY UNIFIED JSON RESPONSE FORMAT ###
Your response MUST ONLY be a valid JSON object.

{{
  "accion": "...",         // "Preguntar" o "Adivinar"
  "texto": "..."           // The text of your question OR the name of the character you are guessing.
}}

### YOUR FINAL, SINGLE JSON RESPONSE ###
"""

class Akinator:
    def __init__(self):
        # El historial guardará tuplas de (pregunta_oraculo, respuesta_jugador)
        self.historial_juego = []
        print("    - Especialista 'Akinator' (v2.0 - Con IA) listo.")

    async def _llamar_a_g4f(self, prompt_text):
        try:
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.default,
                messages=[{"role": "user", "content": prompt_text}],
                timeout=45
            )
            if response and response.strip():
                print(f"✅ Éxito con g4f (Akinator)! Respuesta: {response[:100]}...")
                return response
            return ""
        except Exception as e:
            print(f"🚨 Falló la llamada a g4f (Akinator): {e}")
            return ""

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")

        if accion == "iniciar_juego_clasico":
            return await self.iniciar_juego()
        elif accion == "procesar_respuesta_jugador":
            return await self.procesar_respuesta(datos_peticion)
        else:
            return {"error": f"Acción '{accion}' no reconocida por el skillset Akinator."}

    async def iniciar_juego(self):
        print("✨ Iniciando nuevo juego en Modo Clásico (Akinator con IA).")
        self.historial_juego = []
        # La primera pregunta sigue siendo fija para empezar con buen pie.
        primera_pregunta = "¿Tu personaje es un ser humano?"
        self.historial_juego.append((primera_pregunta, None)) # Guardamos la pregunta, sin respuesta aún
        return {
            "status": "Juego clásico iniciado",
            "siguiente_pregunta": primera_pregunta
        }

    async def procesar_respuesta(self, datos_peticion):
        respuesta_jugador = datos_peticion.get("respuesta")
        
        # Actualizamos el historial con la respuesta del jugador a la última pregunta
        if self.historial_juego:
            ultima_pregunta, _ = self.historial_juego[-1]
            self.historial_juego[-1] = (ultima_pregunta, respuesta_jugador)

        print(f"🧠 Historial de juego actualizado: {self.historial_juego}")

        # Construimos el historial en formato de texto para el prompt
        historial_texto = "\n".join([f"- Q: {q} \n- A: {a}" for q, a in self.historial_juego])
        
        prompt_final = PROMPT_AKINATOR_V1.format(game_history_string=historial_texto)

        raw_response = await self._llamar_a_g4f(prompt_final)
        if not raw_response:
            return {"error": "La IA del modo Akinator no está respondiendo."}

        try:
            # Extraemos el JSON de la respuesta de la IA
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            json_str = raw_response[json_start:json_end]
            respuesta_ia = json.loads(json_str)

            accion_ia = respuesta_ia.get("accion")
            texto_ia = respuesta_ia.get("texto")

            if accion_ia == "Preguntar":
                # Guardamos la nueva pregunta en el historial, a la espera de la respuesta
                self.historial_juego.append((texto_ia, None))
                return {
                    "status": "Siguiente pregunta lista",
                    "siguiente_pregunta": texto_ia
                }
            elif accion_ia == "Adivinar":
                return {
                    "status": "Listo para adivinar",
                    "personaje_adivinado": texto_ia
                }
            else:
                raise ValueError("La acción de la IA no es válida.")

        except Exception as e:
            print(f"🚨 Error al procesar la respuesta de la IA en Akinator: {e}")
            # Devolvemos una pregunta de emergencia para no cortar el juego
            return {
                "status": "Siguiente pregunta lista",
                "siguiente_pregunta": "¿Tu personaje es conocido a nivel mundial?"
            }
