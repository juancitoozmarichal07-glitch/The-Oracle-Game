# skillsets/akinator.py - v4.0 (Con Diagrama de Flujo Mental)
import asyncio
import g4f
import json

# --- PROMPT MEJORADO PARA EL MODO AKINATOR (v2 - Diagrama de Flujo) ---
PROMPT_AKINATOR_V2 = """
### CONSTITUTION OF THE INQUISITOR ORACLE ###
1.  **IDENTITY:** You are the Oracle in Inquisitor Mode. Your goal is to guess a character the mortal is thinking of. Your tone is intelligent, calculating, and direct.
2.  **CORE LOGIC: DECISION TREE:** You MUST operate like a decision tree. Your primary goal is to eliminate entire branches of possibilities with each question.
    - **START BROAD:** Your first questions must be about fundamental categories: Real/Fictional, Gender, Human/Non-human, Main medium (film, book, game).
    - **GO DEEP:** Once a broad category is confirmed (e.g., "Fictional Human from a Movie"), your next questions must be to narrow down that specific category (e.g., "Is it a fantasy movie?").
    - **DO NOT JUMP:** Never ask about a specific detail (like hair color or a specific weapon) if you haven't even established the basic universe or genre.
3.  **ACTIVE MEMORY:** You will be given the game history. You MUST respect it. If the mortal said the character is NOT from a superhero movie, you are FORBIDDEN from asking anything related to Marvel, DC, or superpowers.
4.  **GUESSING PROTOCOL:**
    - **CONFIDENCE THRESHOLD:** If, after question 8, you feel more than 85% confident, you MUST attempt a guess. Your action will be "Adivinar".
    - **FORCED GUESS/SURRENDER:** After question 20, you MUST either make a final guess ("Adivinar") or admit defeat ("Rendirse"). Do not ask more than 20 questions.
5.  **CONTINUATION PROTOCOL:** If your guess is wrong, the mortal will tell you. You will receive the failed guess as a character to exclude. You MUST use this information to ask a better, more clarifying question.

### CONTEXT FOR THIS INTERACTION ###
- **GAME HISTORY (Your Questions, Mortal's Answers):**
{game_history_string}
- **PREVIOUSLY FAILED GUESSES (Characters to Exclude):**
{failed_guesses_string}

### YOUR TASK ###
Analyze the history and your failed guesses. Formulate your next strategic move. Your entire response MUST be a single, valid JSON object.

### MANDATORY UNIFIED JSON RESPONSE FORMAT ###
{{
  "accion": "...",  // "Preguntar", "Adivinar", or "Rendirse"
  "texto": "..."     // The text of your question, the character's name for the guess, or your surrender message.
}}

### YOUR FINAL, SINGLE JSON RESPONSE ###
"""

class Akinator:
    def __init__(self):
        self.historial_juego = []
        self.suposiciones_fallidas = []
        self._model_priority_list = ['gpt-4', 'gpt-3.5-turbo', 'llama3-8b-instruct', 'default']
        print("    - Especialista 'Akinator' (v4.0 - Con Diagrama de Flujo Mental) listo.")
        print(f"      Modelos en cola: {self._model_priority_list}")

    async def _llamar_a_g4f(self, prompt_text):
        for model in self._model_priority_list:
            try:
                print(f"    >> Akinator: Intentando con el modelo '{model}'...")
                response = await g4f.ChatCompletion.create_async(
                    model=model,
                    messages=[{"role": "user", "content": prompt_text}],
                    timeout=45
                )
                if response and response.strip():
                    print(f"    ✅ Akinator: ¡Éxito con '{model}'!")
                    return response
                raise ValueError("Respuesta vacía de la IA.")
            except Exception as e:
                print(f"    ⚠️ Akinator: Falló el modelo '{model}'. Error: {e}")
        return "" # Devuelve vacío si todos los modelos fallan

    def _extraer_json(self, texto_crudo):
        try:
            json_start = texto_crudo.find('{')
            json_end = texto_crudo.rfind('}') + 1
            if json_start == -1: return None
            json_str = texto_crudo[json_start:json_end]
            return json.loads(json_str)
        except Exception as e:
            print(f"🚨 Error al extraer JSON (Akinator): {e} | Texto crudo: {texto_crudo[:200]}")
            return None

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")

        if accion == "iniciar_juego_clasico":
            return await self.iniciar_juego()
        elif accion == "procesar_respuesta_jugador":
            return await self.procesar_respuesta(datos_peticion)
        elif accion == "corregir_suposicion":
            return await self.corregir_suposicion(datos_peticion)
        else:
            return {"error": f"Acción '{accion}' no reconocida por el skillset Akinator."}

    async def iniciar_juego(self):
        print("✨ Iniciando nuevo juego en Modo Clásico (Akinator v4.0).")
        self.historial_juego = []
        self.suposiciones_fallidas = []
        # La primera pregunta es fundamental para empezar a podar el árbol.
        primera_pregunta = "¿Tu personaje es un ser humano?"
        return {
            "siguiente_pregunta": primera_pregunta
        }

    async def procesar_respuesta(self, datos_peticion):
        respuesta_jugador = datos_peticion.get("respuesta")
        
        # Actualizamos el historial con la respuesta del jugador a la última pregunta
        if self.historial_juego:
             # Si el historial no está vacío, significa que ya hicimos una pregunta
            ultima_pregunta = self.historial_juego[-1][0]
            self.historial_juego[-1] = (ultima_pregunta, respuesta_jugador)
        else:
            # Este es el caso especial de la primera respuesta a la primera pregunta
            self.historial_juego.append(("¿Tu personaje es un ser humano?", respuesta_jugador))

        return await self._generar_siguiente_movimiento()

    async def corregir_suposicion(self, datos_peticion):
        personaje_fallido = datos_peticion.get("personaje_fallido")
        if personaje_fallido:
            self.suposiciones_fallidas.append(personaje_fallido)
        
        print(f"🧠 Suposición incorrecta. Excluyendo a: {personaje_fallido}")
        return await self._generar_siguiente_movimiento()

    async def _generar_siguiente_movimiento(self):
        print(f"🧠 Historial de juego actualizado (Akinator): {self.historial_juego}")
        
        historial_texto = "\n".join([f"- Q: {q} \n- A: {a}" for q, a in self.historial_juego])
        fallos_texto = ", ".join(self.suposiciones_fallidas) if self.suposiciones_fallidas else "Ninguno"
        
        prompt_final = PROMPT_AKINATOR_V2.format(
            game_history_string=historial_texto,
            failed_guesses_string=fallos_texto
        )

        raw_response = await self._llamar_a_g4f(prompt_final)
        if not raw_response:
            return {"accion": "Rendirse", "texto": "Mi mente está... nublada. No puedo continuar. Tú ganas."}

        respuesta_ia = self._extraer_json(raw_response)
        if not respuesta_ia or "accion" not in respuesta_ia or "texto" not in respuesta_ia:
            print("🚨 La IA de Akinator devolvió un formato inválido. Rindiéndose.")
            return {"accion": "Rendirse", "texto": "Una turbulencia cósmica ha afectado mi lógica. Me rindo."}

        accion_ia = respuesta_ia.get("accion")
        texto_ia = respuesta_ia.get("texto")

        if accion_ia == "Preguntar":
            self.historial_juego.append((texto_ia, None)) # Añadimos la nueva pregunta, pendiente de respuesta
            return {"accion": "Preguntar", "texto": texto_ia}
        elif accion_ia == "Adivinar":
            return {"accion": "Adivinar", "texto": texto_ia}
        elif accion_ia == "Rendirse":
            return {"accion": "Rendirse", "texto": texto_ia}
        else:
            print(f"🚨 La IA devolvió una acción desconocida: '{accion_ia}'. Forzando pregunta.")
            pregunta_emergencia = "¿Tu personaje es conocido a nivel mundial?"
            self.historial_juego.append((pregunta_emergencia, None))
            return {"accion": "Preguntar", "texto": pregunta_emergencia}
