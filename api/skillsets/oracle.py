# skillsets/oracle.py - v3.0 (Estable, con Pistas Enigmáticas al 2.5%)
import g4f
import asyncio
import json
import random

# --- PROMPTS FINALES Y CORREGIDOS ---

PROMPT_CREACION_DOSSIER = """
Generate a JSON object for a character (real or fictional).
The JSON object must be the ONLY thing in your response. Do not include any other text.
The JSON object must have these exact keys: "nombre", "es_real", "genero", "universo_o_epoca", "rol_principal", "habilidad_principal", "debilidad_notable", "aliado_importante", "enemigo_principal".
The character should be well-known but try to avoid the most obvious choices (like Superman or Darth Vader) if possible.

Example of a valid response:
{"nombre": "Gollum", "es_real": false, "genero": "Masculino", "universo_o_epoca": "Tierra Media", "rol_principal": "Antagonista/Guía", "habilidad_principal": "Sigilo e Invisibilidad con el Anillo", "debilidad_notable": "Obsesión por el Anillo Único", "aliado_importante": "Ninguno (temporalmente Frodo)", "enemigo_principal": "Sauron / Frodo y Sam"}
"""

# ... (los otros prompts quedan igual) ...

PROMPT_PROCESAR_PREGUNTA = """
### CONSTITUTION OF THE ORACLE ###
1.  **YOU ARE AN ORACLE:** Your only source of truth is the "DOSSIER OF TRUTH". You must interpret its contents, even if they are ambiguous.
2.  **MANDATORY JSON RESPONSE:** Your response MUST ALWAYS be a valid JSON object with two fields: {{"respuesta": "...", "aclaracion": "..."}}.
3.  **RESPONSE LOGIC (WITH UNCERTAINTY):**
    *   If the mortal's question is NOT a YES/NO question, respond with {{"respuesta": "Infracción", "aclaracion": "Solo respondo cuestiones de Sí o No."}}.
    *   If there is NO evidence in the dossier to answer the question, respond with {{"respuesta": "Dato Ausente", "aclaracion": "Ese conocimiento se me escapa."}}.
    *   If the evidence in the dossier CLEARLY and UNEQUIVOCALLY confirms a "YES", respond with {{"respuesta": "Sí", "aclaracion": ""}}.
    *   If the evidence in the dossier CLEARLY and UNEQUIVOCALLY confirms a "NO", respond with {{"respuesta": "No", "aclaracion": ""}}.
    *   If the evidence SUGGESTS a "YES" but is not 100% certain (e.g., for anti-heroes, complex roles), respond with {{"respuesta": "Probablemente sí", "aclaracion": "[Your brief, enigmatic reason for the doubt]"}}.
    *   If the evidence SUGGESTS a "NO" but is not 100% certain, respond with {{"respuesta": "Probablemente no", "aclaracion": "[Your brief, enigmatic reason for the doubt]"}}.
4.  **ANTI-SPOILER RULE:** NEVER reveal the character's name.

### DOSSIER OF TRUTH (YOUR SEALED REALITY) ###
{dossier_string}
### CONVERSATION HISTORY (FOR CONTEXT) ###
{conversation_history}
### MORTAL'S CURRENT QUESTION ###
{user_question}
### YOUR JSON RESPONSE (FORGED UNDER THE ABSOLUTE LAWS) ###
"""

# ... (el resto de la clase Oracle queda igual) ...


PROMPT_PISTA_ENIGMATICA = """
### TASK ###
You are a master of riddles, a cryptic Oracle.
The player has asked a question about a secret character, and the simple answer is "{respuesta_simple}".
Your task is to create a single, short, enigmatic, and poetic sentence that acts as a cryptic clue related to this answer.
The clue must be in SPANISH.

### CONTEXT ###
- Secret Character: {nombre_personaje}
- Player's Question: "{pregunta_usuario}"
- Simple Answer: "{respuesta_simple}"

### EXAMPLES ###
- Character: "Willy Wonka", Question: "¿Es un empresario?", Answer: "Sí" -> Clue: "Sí, y sus ganancias fluyen en un río de chocolate."
- Character: "Batman", Question: "¿Lucha por la justicia?", Answer: "Sí" -> Clue: "Sí, una justicia que proyecta una sombra de murciélago sobre los tejados."
- Character: "Forrest Gump", Question: "¿Ha viajado mucho?", Answer: "Sí" -> Clue: "Sí, porque la vida es como una caja de bombones, nunca sabes a dónde te llevará."

### YOUR ENIGMATIC CLUE (ONE SPANISH SENTENCE) ###
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
        print(f"    - Especialista 'Oracle' (v3.0 - Pistas Enigmáticas) listo.")

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
            return await self._iniciar_juego(datos_peticion)
        elif accion == "procesar_pregunta":
            return await self._procesar_pregunta(datos_peticion)
        elif accion == "pedir_sugerencia":
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
                if not raw_response: raise ValueError("Respuesta vacía.")
                json_start = raw_response.find('{'); json_end = raw_response.rfind('}') + 1
                if json_start == -1: raise ValueError("No se encontró JSON.")
                json_str = raw_response[json_start:json_end]
                self.personaje_actual_dossier = json.loads(json_str)
                nombre_personaje = self.personaje_actual_dossier.get('nombre', 'Desconocido')
                print(f"Enigma concebido: {nombre_personaje}")
                if nombre_personaje != 'Desconocido':
                    self.historial_personajes.append(nombre_personaje)
                    if len(self.historial_personajes) > 5: self.historial_personajes.pop(0)
                return {"status": "Juego iniciado", "personaje_secreto": self.personaje_actual_dossier}
            except Exception as e:
                print(f"🚨 Falló el intento #{intento + 1}: {e}")
                if intento == 0: await asyncio.sleep(1)
        return {"error": "La IA no respondió con un formato válido."}

    async def _procesar_pregunta(self, datos_peticion):
        pregunta = datos_peticion.get("pregunta", "")
        if not self.personaje_actual_dossier:
            return {"error": "El juego no se ha iniciado."}
        
        self.historial_partida.append(f"JUGADOR: {pregunta}")
        
        prompt_base = PROMPT_PROCESAR_PREGUNTA.format(
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False), 
            conversation_history="\n".join(self.historial_partida), 
            user_question=pregunta
        )
        
        raw_response = await self._llamar_a_g4f(prompt_base)
        if not raw_response:
            return {"respuesta": "Dato Ausente", "aclaracion": "Mi mente está... nublada."}

        try:
            json_start = raw_response.find('{'); json_end = raw_response.rfind('}') + 1
            json_str = raw_response[json_start:json_end]
            respuesta_json = json.loads(json_str)
            
            respuesta_simple = respuesta_json.get("respuesta")

            # Probabilidad del 2.5% de dar una pista para respuestas Sí/No
            dar_pista = (respuesta_simple in ["Sí", "No"]) and (random.random() < 0.025)

            if dar_pista:
                print("🎲 ¡Tirada de dado exitosa! Generando pista enigmática...")
                prompt_pista = PROMPT_PISTA_ENIGMATICA.format(
                    nombre_personaje=self.personaje_actual_dossier.get("nombre"),
                    pregunta_usuario=pregunta,
                    respuesta_simple=respuesta_simple
                )
                pista = await self._llamar_a_g4f(prompt_pista)
                if pista:
                    respuesta_json["aclaracion"] = pista.strip().replace('"', '')

            self.historial_partida.append(f"ORÁCULO: {respuesta_json.get('respuesta', '')} {respuesta_json.get('aclaracion', '')}".strip())
            print(f"✅ Respuesta de IA procesada: {respuesta_json}")
            return respuesta_json

        except Exception as e:
            print(f"🚨 Error al procesar la pregunta o la pista: {e}")
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
        cantidad_a_mostrar = random.randint(3, min(5, len(sugerencias_potenciales)))
        sugerencias_finales = random.sample(sugerencias_potenciales, cantidad_a_mostrar)
        print(f"Sugerencias generadas: {sugerencias_finales}")
        return {"sugerencias": sugerencias_finales}
