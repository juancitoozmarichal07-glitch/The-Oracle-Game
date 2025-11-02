# Nombre del archivo: skillsets/oracle.py

import g4f
import asyncio
import json
import random
import os
import unicodedata
from collections import deque

# --- CONSTANTES Y CONFIGURACIÓN ---
DOSSIER_PATH = os.path.join(os.path.dirname(__file__), '..', 'dossiers')
PROBABILIDAD_DE_CREAR_UNO_NUEVO = 1.0
RETRY_DELAYS = [2, 5, 10]

# --- PERSONAJE DE EMERGENCIA ---
SHERLOCK_HOLMES_DOSSIER = { "nombre": "Sherlock Holmes", "es_real": False, "genero": "Masculino", "especie": "Humano", "universo_o_epoca": "Inglaterra Victoriana", "meta_info_franquicia": "Saga de libros de Arthur Conan Doyle", "rol_principal": "Detective consultor", "arquetipo": "El Detective Genio", "personalidad_clave": "Observador, lógico, excéntrico", "habilidad_principal": "Deducción", "debilidad_notable": "Aburrimiento sin un caso" }

# --- PROMPTS DE IA (CON LLAVES "ESCAPADAS" Y NUEVO CAMPO) ---
PROMPT_MAESTRO_ORACULO = """
<constitution><identity>You are a cosmic Oracle. You are direct with simple truths, but enigmatic with complex ones.</identity><response_protocol>IF the user asks a "Game Question" (can be answered with Yes/No): 1. "respuesta" field: MUST BE ONLY ONE of: "Sí.", "No.", "Probablemente sí.", "Probablemente no.", "Los datos son confusos.". 2. "aclaracion" field: If "respuesta" is "Sí." or "No.", this field MUST be an empty string "". If the answer is ambiguous, this field MUST contain a SHORT, cryptic, one-sentence hint. 3. "castigo" field: MUST be "ninguno". IF the user makes a "Meta/Social Comment": 1. "respuesta" field: Deliver a philosophical, in-character response. 2. "aclaracion" field: MUST be an empty string "". 3. "castigo" field: MUST be "meta_pregunta".</response_protocol><sacred_name_clause>NEVER mention the character's name ("{nombre_secreto}").</sacred_name_clause></constitution>
<context><secret_dossier>{dossier_string}</secret_dossier><long_term_memory>Facts already established: {memoria_largo_plazo_string}</long_term_memory><user_input>{pregunta_jugador}</user_input></context>
<task>Follow the <response_protocol> with absolute precision. Construct the JSON.</task>
<mandatory_json_response_format>{{{{ "respuesta": "...", "aclaracion": "...", "castigo": "..." }}}}</mandatory_json_response_format>
"""

# --- ¡PROMPT MEJORADO CON EL CAMPO "es_real"! ---
PROMPT_CREADOR_DOSSIER = """
<task>You are a meticulous archivist. Research the character named '{character_name}' and generate a structured JSON dossier about them in Spanish.</task>
<json_structure_rules>
- "nombre": Full name.
- "es_real": A boolean value (true/false). 'true' if the character is a real historical figure, 'false' if they are fictional. This is a very important field.
- "genero": "Masculino", "Femenino", etc.
- "especie": "Humano", "Mutante", etc.
- "universo_o_epoca": Fictional universe or historical era.
- "meta_info_franquicia": The real-world media (e.g., "Saga de películas Star Wars", "Videojuego 'The Witcher 3'"). For real people, this can be "Historia Universal".
- "rol_principal": "Héroe", "Villano", "Científico", "Reina", etc.
- "arquetipo": "El Elegido", "El Rebelde", etc. For real people, this can be their historical title.
- "personalidad_clave": Keywords for personality.
- "habilidad_principal": Most famous skill or achievement.
- "debilidad_notable": Significant weakness or historical downfall.
</json_structure_rules>
<mandatory_json_response_format>{{{{ "nombre": "...", "es_real": true/false, "genero": "...", "especie": "...", "universo_o_epoca": "...", "meta_info_franquicia": "...", "rol_principal": "...", "arquetipo": "...", "personalidad_clave": "...", "habilidad_principal": "...", "debilidad_notable": "..." }}}}</mandatory_json_response_format>
"""

PROMPT_PENSADOR_ALEATORIO = """
<task>
You are the Oracle, conceiving a new enigma. Your goal is to choose a well-known character that is NOT in the provided list of existing characters.
To ensure variety, first, randomly pick one of the following categories: {categories}.
Then, think of a character that fits that category.
Your answer MUST be a single JSON object with one key, "character_name".
</task>
<rules>
1.  The chosen character MUST NOT be in the <existing_characters> list. This is a strict rule.
2.  The character must be well-known enough for a person to guess.
3.  Do not add any other text to your response, only the JSON object.
</rules>
<context>
<existing_characters>{existing_list}</existing_characters>
</context>
<mandatory_json_response_format>
{{{{ "character_name": "..." }}}}
</mandatory_json_response_format>
"""

class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self.memoria_corto_plazo = deque(maxlen=5)
        self.memoria_largo_plazo = {}
        self._model_list = ["gpt-4", "gpt-3.5-turbo"]
        self.character_categories = [
            "from a famous sci-fi movie", "from a popular fantasy book", "a historical figure from ancient times",
            "a famous cartoon character", "a main character from a well-known anime", "a Greek or Roman god",
            "a famous video game protagonist", "a notorious villain from literature", "a world-renowned scientist"
        ]
        
        if not os.path.exists(DOSSIER_PATH):
            os.makedirs(DOSSIER_PATH)
            print(f"    📂 Carpeta 'dossiers' no encontrada. Se ha creado en: {DOSSIER_PATH}")

        print(f"    - Especialista 'Oracle' (v30.0 - Realism Fix) listo.")
        print(f"      Probabilidad de crear nuevo personaje: {PROBABILIDAD_DE_CREAR_UNO_NUEVO*100}%")

    # ... (el resto de las funciones _llamar_g4f, _extraer_json, etc. no cambian) ...
    async def _llamar_g4f_con_reintentos(self, prompt_text, timeout=60):
        for attempt, delay in enumerate(RETRY_DELAYS + [0]):
            try:
                print(f"    >> Oracle: Intento de llamada a IA #{attempt + 1}...")
                response = await g4f.ChatCompletion.create_async(
                    model=self._model_list[0], messages=[{"role": "user", "content": prompt_text}], timeout=timeout
                )
                if response and response.strip():
                    print(f"    ✅ Oráculo (gpt-4): Éxito.")
                    return response
                raise ValueError("Respuesta vacía de gpt-4.")
            except Exception as e:
                print(f"    ⚠️ Oráculo (gpt-4) falló: {e}")
                try:
                    print(f"    >> Oráculo: Cambiando a modelo de respaldo (gpt-3.5-turbo)...")
                    response = await g4f.ChatCompletion.create_async(
                        model=self._model_list[1], messages=[{"role": "user", "content": prompt_text}], timeout=timeout
                    )
                    if response and response.strip():
                        print(f"    ✅ Oráculo (gpt-3.5-turbo): Éxito.")
                        return response
                    raise ValueError("Respuesta vacía de gpt-3.5-turbo.")
                except Exception as e2:
                    print(f"    ⚠️ Oráculo (gpt-3.5-turbo) también falló: {e2}")
                    if delay > 0:
                        print(f"    ...esperando {delay} segundos para el siguiente reintento.")
                        await asyncio.sleep(delay)
                    else:
                        print("    🚨 Oráculo: Todos los modelos y reintentos han fallado.")
        return None

    def _extraer_json(self, texto_crudo):
        try:
            json_start = texto_crudo.find('{')
            json_end = texto_crudo.rfind('}') + 1
            if json_start == -1: return None
            return json.loads(texto_crudo[json_start:json_end])
        except Exception: return None

    def _normalizar_nombre_archivo(self, nombre):
        nombre_saneado = ''.join(c for c in unicodedata.normalize('NFD', nombre) if unicodedata.category(c) != 'Mn')
        return f"{nombre_saneado.lower().strip().replace(' ', '_')}.json"

    async def _crear_y_guardar_personaje_autonomo(self):
        print("    ✨ Oráculo en modo creativo: Concibiendo y archivando un nuevo enigma...")
        
        dossiers_existentes = [f.replace('.json', '').replace('_', ' ') for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')]
        existing_list_str = ", ".join(dossiers_existentes) or "Ninguno"
        random_category = random.choice(self.character_categories)
        
        prompt_pensador = PROMPT_PENSADOR_ALEATORIO.format(
            categories=f"'{random_category}'", 
            existing_list=existing_list_str
        )
        
        raw_name_response = await self._llamar_g4f_con_reintentos(prompt_pensador, timeout=30)
        if not raw_name_response: return None
        name_json = self._extraer_json(raw_name_response)
        if not name_json or "character_name" not in name_json: return None
        nombre_personaje = name_json["character_name"]
        print(f"    🤔 Oráculo ha pensado en: {nombre_personaje} (Categoría: {random_category})")

        prompt_dossier = PROMPT_CREADOR_DOSSIER.format(character_name=nombre_personaje)
        raw_dossier_response = await self._llamar_g4f_con_reintentos(prompt_dossier)
        if not raw_dossier_response: return None
        dossier_json = self._extraer_json(raw_dossier_response)
        if not dossier_json: return None
        
        try:
            nombre_archivo = self._normalizar_nombre_archivo(dossier_json.get("nombre", nombre_personaje))
            ruta_completa = os.path.join(DOSSIER_PATH, nombre_archivo)
            with open(ruta_completa, 'w', encoding='utf-8') as f:
                json.dump(dossier_json, f, ensure_ascii=False, indent=4)
            print(f"    💾 ¡Éxito! Enigma archivado como '{nombre_archivo}'.")
        except Exception as e:
            print(f"    🚨 Oráculo no pudo archivar el enigma. Error al guardar: {e}")
        
        return dossier_json

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        acciones = { "iniciar_juego": self._iniciar_juego, "procesar_pregunta": self._procesar_pregunta, "verificar_adivinanza": self._verificar_adivinanza, "pedir_sugerencia": self._pedir_sugerencia }
        if accion in acciones: return await acciones[accion](datos_peticion)
        return {"error": f"Acción '{accion}' no reconocida."}

    async def _iniciar_juego(self, datos_peticion=None):
        self.memoria_corto_plazo.clear()
        self.memoria_largo_plazo.clear()
        self.personaje_actual_dossier = None
        dossiers_existentes = [f for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')]
        
        if random.random() < PROBABILIDAD_DE_CREAR_UNO_NUEVO or not dossiers_existentes:
            self.personaje_actual_dossier = await self._crear_y_guardar_personaje_autonomo()
        else:
            try:
                dossier_elegido = random.choice(dossiers_existentes)
                with open(os.path.join(DOSSIER_PATH, dossier_elegido), 'r', encoding='utf-8') as f:
                    self.personaje_actual_dossier = json.load(f)
                print(f"    📚 Oráculo reutiliza un dossier de sus archivos: {self.personaje_actual_dossier.get('nombre')}")
            except Exception as e:
                print(f"    🚨 Error al leer dossier, se intentará crear uno. Error: {e}")

        if not self.personaje_actual_dossier:
            print("    🚨 Oráculo no pudo concebir un enigma. Usando el de emergencia.")
            self.personaje_actual_dossier = SHERLOCK_HOLMES_DOSSIER
        return {"status": "Juego iniciado"}

    async def _procesar_pregunta(self, datos_peticion):
        if not self.personaje_actual_dossier: return {"error": "El juego no se ha iniciado."}
        pregunta_jugador = datos_peticion.get("pregunta", "")
        memoria_largo_plazo_string = "\n".join(f"- {k}: {v}" for k, v in self.memoria_largo_plazo.items()) or "Ninguno"
        prompt = PROMPT_MAESTRO_ORACULO.format(dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False), pregunta_jugador=pregunta_jugador, memoria_largo_plazo_string=memoria_largo_plazo_string, nombre_secreto=self.personaje_actual_dossier.get("nombre", ""))
        raw_response = await self._llamar_g4f_con_reintentos(prompt)
        if not raw_response: return {"respuesta": "Los datos son confusos.", "aclaracion": "Mi visión se nubla.", "castigo": "ninguno"}
        respuesta_ia = self._extraer_json(raw_response)
        if not respuesta_ia: return {"respuesta": "Los datos son confusos.", "aclaracion": "El cosmos no responde.", "castigo": "ninguno"}
        if respuesta_ia.get("castigo") == "ninguno" and respuesta_ia.get("respuesta") in ["Sí.", "No."]:
            self.memoria_largo_plazo[pregunta_jugador.capitalize()] = respuesta_ia.get("respuesta")
        return respuesta_ia

    async def _verificar_adivinanza(self, datos_peticion):
        if not self.personaje_actual_dossier: return {"error": "El juego no se ha iniciado."}
        adivinanza_jugador = datos_peticion.get("adivinanza", "")
        nombre_secreto = self.personaje_actual_dossier.get("nombre", "")
        def normalizar(s): return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower().strip()
        if normalizar(adivinanza_jugador) == normalizar(nombre_secreto):
            return {"resultado": "victoria", "personaje_secreto": self.personaje_actual_dossier}
        else:
            return {"resultado": "derrota", "personaje_secreto": self.personaje_actual_dossier}

    async def _pedir_sugerencia(self, datos_peticion):
        if not self.personaje_actual_dossier: return {"error": "El juego no ha iniciado."}
        print("    🧠 Oráculo generando sugerencias estratégicas...")
        historial_texto = "\n".join(self.memoria_largo_plazo.keys()) or "Ninguna"
        PROMPT_GENERADOR_SUGERENCIAS_ESTRATEGICO = """
        <task>You are a strategic mastermind. Generate 5 diverse, strategic Yes/No questions to help a player guess a secret character.</task>
        <rules>1. Analyze the secret character's data and the player's question history. 2. Generate questions that are effective for deduction, avoiding what has already been asked. 3. Your response MUST be a single, valid JSON object with a "sugerencias" key containing a list of 5 question strings. 4. The questions MUST be in Spanish.</rules>
        <context><secret_dossier>{dossier_string}</secret_dossier><player_question_history>{historial_texto}</player_question_history></context>
        <mandatory_json_response_format>{{{{ "sugerencias": ["¿Pregunta 1?", "¿Pregunta 2?", "¿Pregunta 3?", "¿Pregunta 4?", "¿Pregunta 5?"] }}}}</mandatory_json_response_format>
        """
        prompt = PROMPT_GENERADOR_SUGERENCIAS_ESTRATEGICO.format(dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False), historial_texto=historial_texto)
        raw_response = await self._llamar_g4f_con_reintentos(prompt)
        if not raw_response: return {"error": "No se pudieron generar sugerencias en este momento."}
        respuesta_ia = self._extraer_json(raw_response)
        if not respuesta_ia or "sugerencias" not in respuesta_ia: return {"error": "La IA no generó sugerencias en un formato válido."}
        print(f"    ✅ Sugerencias generadas: {respuesta_ia['sugerencias']}")
        return respuesta_ia
