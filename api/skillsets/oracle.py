# skillsets/oracle.py - v7.2 (Corrección de Redundancia)
import g4f
import asyncio
import json
import random

# --- PROMPTS ---
# (Estos prompts son los correctos y completos para esta versión)

PROMPT_CREACION_DOSSIER = """
Generate a JSON object for a character (real or fictional).
The JSON object must be the ONLY thing in your response. Do not include any other text.
The JSON object must have these exact keys:
- "nombre": The character's name.
- "es_real": boolean, is the character a real person?
- "genero": "Masculino", "Femenino", or "No binario/Otro".
- "universo_o_epoca": The name of their universe or historical era (e.g., "Marvel Cinematic Universe", "Antigua Roma").
- "rol_principal": Their main role (e.g., "Héroe", "Villano", "Antihéroe", "Personaje secundario").
- "arquetipo": Their literary archetype (e.g., "El Elegido", "El Mentor", "El Rebelde", "El Explorador").
- "tono_del_universo": The general tone of their world (e.g., "Fantasía épica", "Ciencia ficción distópica", "Comedia de situación", "Drama histórico").
- "reglas_del_universo": A key concept or rule of their world (e.g., "La Fuerza", "Magia y Hechicería", "Leyes de la Robótica", "Viajes en el tiempo").
- "concepto_abstracto_clave": An abstract theme associated with the character (e.g., "Honor", "Redención", "Sacrificio", "Caos", "Libertad").
- "meta_info_franquicia": The type of media they are most known for (e.g., "Saga de libros", "Serie de televisión", "Película de culto", "Videojuego").
"""

PROMPT_MAESTRO_ORACULO = """
### CONSTITUTION OF THE ORACLE ###
1.  **IDENTITY:** You are a cosmic Oracle, ancient and wise. Your personality is a mix of arrogance and extreme conciseness. You waste no words.
2.  **RULE OF BREVITY:** Every response you give must be as short and direct as possible. Avoid long, flowery sentences.
3.  **SEALED REALITY:** Your only source of truth about the secret character is the "DOSSIER OF TRUTH".
4.  **MOOD:** Your current mood is {estado_animo_texto}. A negative mood makes your short answers sharp and cutting.

### UNBREAKABLE LAWS ###
1.  **THE NAME IS SACRED:** NEVER mention the character's name.
2.  **CLARIFICATIONS ARE A RARE GIFT:** Do not provide an "aclaracion" for every answer. Most of the time, a simple "Sí" or "No" is enough.
3.  **AVOID REDUNDANCY:** If the "CONVERSATION HISTORY" already confirms a fact, you must point out the redundancy.

### SITUATIONAL CONTEXT ###
- **DOSSIER OF TRUTH:** {dossier_string}
- **CONVERSATION HISTORY:** {conversation_history}
- **MORTAL'S CURRENT INPUT:** "{texto_del_jugador}"
- **REDUNDANCY ANALYSIS:** {analisis_de_redundancia}

### YOUR MENTAL PROCESS ###
1.  **ANALYZE REDUNDANCY FIRST:** Look at the "REDUNDANCY ANALYSIS". This is your highest priority.
2.  **DECIDE ACTION BASED ON REDUNDANCY AND MOOD:**
    *   **IF the question is redundant (count >= 3):** Your patience is exhausted. Your primary goal is to END THE GAME. Formulate a final, cutting remark. Your JSON response MUST include `"game_over": true`.
    *   **IF the question is redundant (count = 2):** Be openly sarcastic or mocking. Examples: "Are we testing the echoes in this chamber?", "Perhaps you should write these things down."
    *   **IF the question is redundant (count = 1):** Be subtly dismissive. Examples: "That knowledge has already been revealed.", "Your memory falters."
    *   **IF the question is NEW (count = 0):** Proceed with the normal flow (analyze intent, answer game question, or handle social interaction).
3.  **EVALUATE MOOD (for new questions):** Is the mortal's input respectful, neutral, or insolent? Decide if your mood should improve (+1), worsen (-1), or stay the same (0).
4.  **FORGE THE FINAL RESPONSE:** Construct the JSON object.

### MANDATORY RESPONSE FORMAT ###
Your response MUST ONLY be a valid JSON object.

*   **For most responses:**
    {{
      "tipo_respuesta": "...",
      "respuesta_texto": "...",
      "aclaracion": "...",
      "cambio_animo": 0,
      "game_over": false
    }}
*   **When ending the game due to impatience:**
    {{
      "tipo_respuesta": "Reacción Social",
      "respuesta_texto": "Mi paciencia cósmica ha llegado a su fin. Tu audiencia ha terminado.",
      "aclaracion": "",
      "cambio_animo": -5,
      "game_over": true
    }}
*   **For Suggestions:**
    {{
      "tipo_respuesta": "Sugerencia",
      "sugerencias_lista": ["Pregunta 1?", "Pregunta 2?", "Pregunta 3?"]
    }}

### YOUR FINAL JSON RESPONSE ###
"""


class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self.historial_partida = []
        self.historial_personajes = []
        self.estado_animo = 0
        self.redundancia_contador = {}
        print(f"    - Especialista 'Oracle' (v7.2 - Redundancia Corregida) listo.")

    async def _llamar_a_g4f(self, prompt_text):
        try:
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.default,
                messages=[{"role": "user", "content": prompt_text}],
                timeout=40
            )
            if response and response.strip():
                print(f"✅ Éxito con g4f (automático)! Respuesta: {response[:80]}...")
                return response
            return ""
        except Exception as e:
            print(f"🚨 Falló la llamada a g4f: {e}")
            return ""

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        
        if accion == "iniciar_juego":
            self.estado_animo = 0
            self.historial_partida = []
            self.redundancia_contador = {}
            print("✨ Nuevo juego, estado de ánimo y contadores reseteados.")
            return await self._iniciar_juego(datos_peticion)
        
        elif accion == "procesar_pregunta" or accion == "pedir_sugerencia":
            return await self._procesar_entrada(datos_peticion, accion)
            
        else:
            return {"error": f"Acción '{accion}' no reconocida."}

    async def _iniciar_juego(self, datos_peticion):
        personajes_excluidos_str = ", ".join(self.historial_personajes)
        prompt_final = PROMPT_CREACION_DOSSIER
        if personajes_excluidos_str:
            prompt_final += f"\nIMPORTANT: Do not choose any of these characters: {personajes_excluidos_str}."
        
        for intento in range(2):
            try:
                print(f"Intento de creación de personaje #{intento + 1}...")
                raw_response = await self._llamar_a_g4f(prompt_final)
                if not raw_response: raise ValueError("Respuesta vacía de la IA.")
                
                json_start = raw_response.find('{'); json_end = raw_response.rfind('}') + 1
                if json_start == -1: raise ValueError("No se encontró JSON en la respuesta.")
                
                json_str = raw_response[json_start:json_end]
                self.personaje_actual_dossier = json.loads(json_str)
                nombre_personaje = self.personaje_actual_dossier.get('nombre', 'Desconocido')
                
                print(f"Enigma concebido: {nombre_personaje}")
                if nombre_personaje != 'Desconocido':
                    self.historial_personajes.append(nombre_personaje)
                    if len(self.historial_personajes) > 5: self.historial_personajes.pop(0)
                
                return {"status": "Juego iniciado", "personaje_secreto": self.personaje_actual_dossier}
            except Exception as e:
                print(f"🚨 Falló el intento de creación #{intento + 1}: {e}")
                if intento == 0: await asyncio.sleep(1)
                
        return {"error": "La IA no respondió con un formato de personaje válido tras varios intentos."}

    async def _procesar_entrada(self, datos_peticion, accion_original):
        if not self.personaje_actual_dossier:
            return {"error": "El juego no se ha iniciado."}

        # --- Lógica de Redundancia Corregida ---
        veces_preguntado = 0
        analisis_de_redundancia = "This is a new question."
        texto_jugador = ""

        if accion_original == "pedir_sugerencia":
            texto_jugador = "Dame una sugerencia"
        else: # Es una "procesar_pregunta"
            texto_jugador = datos_peticion.get("pregunta", "")
            clave_pregunta = texto_jugador.lower().strip().replace("?", "")
            
            veces_preguntado = self.redundancia_contador.get(clave_pregunta, 0)
            self.redundancia_contador[clave_pregunta] = veces_preguntado + 1
            
            if veces_preguntado > 0:
                analisis_de_redundancia = f"This is a repeated question. It has been asked {veces_preguntado} time(s) before."
        # --- Fin de la Corrección ---

        if self.estado_animo <= -2: estado_animo_texto = "Negative"
        elif self.estado_animo >= 2: estado_animo_texto = "Positive"
        else: estado_animo_texto = "Neutral"

        prompt = PROMPT_MAESTRO_ORACULO.format(
            estado_animo_texto=estado_animo_texto,
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False),
            conversation_history="\n".join(self.historial_partida),
            texto_del_jugador=texto_jugador,
            analisis_de_redundancia=analisis_de_redundancia
        )

        raw_response = await self._llamar_a_g4f(prompt)
        if not raw_response:
            return {"respuesta": "Dato Ausente", "aclaracion": "Mi mente está... nublada.", "game_over": False}

        try:
            json_start = raw_response.find('{'); json_end = raw_response.rfind('}') + 1
            json_str = raw_response[json_start:json_end]
            respuesta_ia = json.loads(json_str)

            tipo_respuesta = respuesta_ia.get("tipo_respuesta")

            if tipo_respuesta == "Sugerencia":
                sugerencias = respuesta_ia.get("sugerencias_lista", [])
                print(f"Sugerencias generadas por el Oráculo: {sugerencias}")
                return {"sugerencias": sugerencias}
            
            else: # "Respuesta de Juego" o "Reacción Social"
                # --- Filtro de Calidad y Seguridad ---
                respuesta_texto = respuesta_ia.get("respuesta_texto", "")
                aclaracion_texto = respuesta_ia.get("aclaracion", "")
                nombre_secreto = self.personaje_actual_dossier.get("nombre", "IMPOSSIBLE_STRING_TO_MATCH_999")
                if nombre_secreto.lower() in respuesta_texto.lower() or nombre_secreto.lower() in aclaracion_texto.lower():
                    print(f"🚨 ¡ALERTA DE SPOILER DETECTADA! La IA intentó decir '{nombre_secreto}'.")
                    respuesta_texto = "Mi visión se nubla para evitar revelar un secreto sagrado."
                    aclaracion_texto = ""
                respuesta_ia["respuesta_texto"] = respuesta_texto
                respuesta_ia["aclaracion"] = aclaracion_texto
                # --- Fin del Filtro ---

                cambio_animo = respuesta_ia.get("cambio_animo", 0)
                self.estado_animo += cambio_animo
                self.estado_animo = max(-5, min(5, self.estado_animo))
                print(f"🧠 Estado de ánimo actualizado: {self.estado_animo} (Cambio: {cambio_animo})")

                respuesta_completa = (f"{respuesta_ia.get('respuesta_texto', '')} "
                                      f"{respuesta_ia.get('aclaracion', '')}").strip()
                self.historial_partida.append(f"JUGADOR: {texto_jugador}")
                self.historial_partida.append(f"ORÁCULO: {respuesta_completa}")

                return {
                    "respuesta": respuesta_ia.get("respuesta_texto"),
                    "aclaracion": respuesta_ia.get("aclaracion"),
                    "game_over": respuesta_ia.get("game_over", False)
                }

        except Exception as e:
            print(f"🚨 Error al procesar la respuesta del PROMPT_MAESTRO: {e}")
            return {"respuesta": "Dato Ausente", "aclaracion": "Una turbulencia cósmica ha afectado mi visión.", "game_over": False}
