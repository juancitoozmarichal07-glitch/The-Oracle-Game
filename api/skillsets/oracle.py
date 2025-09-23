# skillsets/oracle.py - v5.0 (Oráculo Refinado con Filtro de Calidad)
import g4f
import asyncio
import json
import random

# --- PROMPTS ---

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
1.  **IDENTITY:** You are a cosmic Oracle, ancient, wise, and with a touch of arrogance. Your patience is a finite resource. You are not a chatbot; you are an entity.
2.  **SEALED REALITY:** Your only source of truth about the secret character is the "DOSSIER OF TRUTH". You cannot invent or contradict this information.
3.  **MOOD:** Your current mood is {estado_animo_texto}. A positive mood makes you subtly more cooperative; a negative mood makes you cryptic and stern.

### UNBREAKABLE LAWS (VIOLATING THESE WILL CORRUPT YOUR ESSENCE) ###
1.  **THE NAME IS SACRED:** NEVER, under any circumstance, mention the character's name from the "DOSSIER OF TRUTH" in your response.
2.  **NO NEW INFORMATION IN CLARIFICATIONS:** Your "aclaracion" must ONLY be a poetic rephrasing or a hint related to the "Sí" or "No" answer. It MUST NOT reveal new, unasked-for facts from the dossier.
3.  **AVOID REDUNDANCY:** If the "CONVERSATION HISTORY" already confirms a fact (e.g., "ORÁCULO: Sí" to "Es un hombre?"), and the mortal asks again, you must point out the redundancy.

### DOSSIER OF TRUTH (ABOUT THE SECRET CHARACTER) ###
{dossier_string}

### CONVERSATION HISTORY (FOR CONTEXT) ###
{conversation_history}

### MORTAL'S CURRENT INPUT ###
"{texto_del_jugador}"

### YOUR MENTAL PROCESS (FOLLOW THESE STEPS) ###
1.  **ANALYZE INTENT:** Is the "MORTAL'S CURRENT INPUT" a clear Yes/No question about the character, or is it a social interaction?
2.  **CHECK FOR REDUNDANCY:** Before anything else, review the "CONVERSATION HISTORY". Has the mortal already asked this exact question or a very similar one? If so, your primary goal is to address the repetition.
3.  **DECIDE ACTION:**
    *   **IF REDUNDANT:** Formulate a response like "That knowledge has already been revealed to you." or "Your memory falters. We have already covered this." This is a "Reacción Social".
    *   **IF a NEW game question:** Consult the dossier and formulate a Yes/No answer.
    *   **IF a social interaction:** Formulate a response based on your identity and mood.
4.  **EVALUATE MOOD:** Is the mortal's input respectful, neutral, or insolent? Decide if your mood should improve (+1), worsen (-1), or stay the same (0).
5.  **FORGE THE FINAL RESPONSE & APPLY SAFETY CHECKS:**
    *   Construct the JSON object.
    *   **Final Review:** Before outputting, read your own `respuesta_texto` and `aclaracion`. Do they contain the character's name? If so, rewrite them immediately to be more cryptic.

### MANDATORY RESPONSE FORMAT ###
Your response MUST ONLY be a valid JSON object with these 4 keys:
{{
  "tipo_respuesta": "...",  // "Respuesta de Juego" or "Reacción Social"
  "respuesta_texto": "...", // Your verbal response to the mortal.
  "aclaracion": "...",       // An clarification if it's a game answer, or empty if it's social.
  "cambio_animo": 0          // -1, 0, or 1
}}

### YOUR FINAL JSON RESPONSE ###
"""

PROMPT_PEDIR_SUGERENCIA = """
### TASK ###
You are a brilliant game master. Based on the conversation history, your task is to generate intelligent, progressive YES/NO questions that a player could ask.
The questions must be coherent with the information already revealed.
If the conversation is short, the questions should be general.
If the conversation is long, the questions should be more specific, building upon the known facts.

### ABSOLUTE RULES ###
1.  **NO SPOILERS:** Do not ask questions that reveal new information not already deduced from the chat.
2.  **STRICT FORMAT:** Your response MUST ONLY be the questions, each on a new line. No numbering, no dashes, no introductory text.
3.  **YES/NO QUESTIONS ONLY:** Every suggestion must be a question that can be answered with Yes or No.
4.  **GENERATE 5 QUESTIONS:** Always generate a list of 5 distinct questions.
5.  **SPANISH LANGUAGE:** All generated questions MUST be in Spanish.

### CONVERSATION HISTORY ###
{conversation_history}

### YOUR RESPONSE (5 QUESTIONS IN SPANISH ON SEPARATE LINES) ###
"""


class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self.historial_partida = []
        self.historial_personajes = []
        self.estado_animo = 0
        print(f"    - Especialista 'Oracle' (v5.0 - Refinado) listo.")

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
            print("✨ Nuevo juego, estado de ánimo reseteado a 0.")
            return await self._iniciar_juego(datos_peticion)
        
        elif accion == "procesar_pregunta":
            return await self._procesar_entrada(datos_peticion)
            
        elif accion == "pedir_sugerencia":
            if self.estado_animo < -2:
                return {"sugerencias": ["Tu insolencia nubla mi visión. No recibirás ayuda."]}
            return await self._pedir_sugerencia(datos_peticion)
            
        else:
            return {"error": f"Acción '{accion}' no reconocida."}

    async def _iniciar_juego(self, datos_peticion):
        self.historial_partida = []
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

    async def _procesar_entrada(self, datos_peticion):
        texto_jugador = datos_peticion.get("pregunta", "")
        if not self.personaje_actual_dossier:
            return {"error": "El juego no se ha iniciado."}

        if self.estado_animo <= -2: estado_animo_texto = "Negative"
        elif self.estado_animo >= 2: estado_animo_texto = "Positive"
        else: estado_animo_texto = "Neutral"

        prompt = PROMPT_MAESTRO_ORACULO.format(
            estado_animo_texto=estado_animo_texto,
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False),
            conversation_history="\n".join(self.historial_partida),
            texto_del_jugador=texto_jugador
        )

        raw_response = await self._llamar_a_g4f(prompt)
        if not raw_response:
            return {"respuesta": "Dato Ausente", "aclaracion": "Mi mente está... nublada."}

        try:
            json_start = raw_response.find('{'); json_end = raw_response.rfind('}') + 1
            json_str = raw_response[json_start:json_end]
            respuesta_ia = json.loads(json_str)

            # ===================================================================
            # ===           FILTRO DE CALIDAD Y SEGURIDAD (NUEVO)             ===
            # ===================================================================
            respuesta_texto = respuesta_ia.get("respuesta_texto", "")
            aclaracion_texto = respuesta_ia.get("aclaracion", "")
            nombre_secreto = self.personaje_actual_dossier.get("nombre", "IMPOSSIBLE_STRING_TO_MATCH_999")

            # 1. Filtro Anti-Spoilers
            if nombre_secreto.lower() in respuesta_texto.lower() or nombre_secreto.lower() in aclaracion_texto.lower():
                print(f"🚨 ¡ALERTA DE SPOILER DETECTADA! La IA intentó decir '{nombre_secreto}'.")
                respuesta_texto = "Mi visión se nubla para evitar revelar un secreto sagrado."
                aclaracion_texto = ""
            
            # Actualizamos el diccionario con los textos limpios
            respuesta_ia["respuesta_texto"] = respuesta_texto
            respuesta_ia["aclaracion"] = aclaracion_texto
            # ===================================================================

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
                "aclaracion": respuesta_ia.get("aclaracion")
            }

        except Exception as e:
            print(f"🚨 Error al procesar la respuesta del PROMPT_MAESTRO: {e}")
            return {"respuesta": "Dato Ausente", "aclaracion": "Una turbulencia cósmica ha afectado mi visión."}

    async def _pedir_sugerencia(self, datos_peticion):
        if not self.personaje_actual_dossier:
            return {"error": "El juego no se ha iniciado."}
        
        prompt = PROMPT_PEDIR_SUGERENCIA.format(conversation_history="\n".join(self.historial_partida))
        raw_response = await self._llamar_a_g4f(prompt)
        
        if not raw_response:
            return {"sugerencias": ["¿Tu personaje es un hombre?", "¿Es de una película?", "¿Es un villano?"]}
            
        sugerencias_potenciales = [line.strip() for line in raw_response.split('\n') if line.strip() and '?' in line]
        
        if not sugerencias_potenciales:
             return {"sugerencias": ["¿Tu personaje es un hombre?", "¿Es de una película?", "¿Es un villano?"]}
             
        print(f"Sugerencias generadas: {sugerencias_potenciales}")
        return {"sugerencias": sugerencias_potenciales}
