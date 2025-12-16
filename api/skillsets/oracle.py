# skillsets/oracle.py - v30.4 (Memoria Activa por Manus)

import g4f
import asyncio
import json
import random
import os
import unicodedata
import re
import time
from collections import deque

# --- CONSTANTES Y CONFIGURACIÓN ---
DOSSIER_PATH = os.path.join(os.path.dirname(__file__), '..', 'dossiers')
PROBABILIDAD_DE_CREAR_UNO_NUEVO = 1.0

# --- PERSONAJE DE EMERGENCIA (PLAN C) ---
SHERLOCK_HOLMES_DOSSIER = { "nombre": "Sherlock Holmes", "es_real": False, "genero": "Masculino", "especie": "Humano", "universo_o_epoca": "Inglaterra Victoriana", "meta_info_franquicia": "Saga de libros de Arthur Conan Doyle", "rol_principal": "Detective consultor", "arquetipo": "El Detective Genio", "personalidad_clave": "Observador, lógico, excéntrico", "habilidad_principal": "Deducción", "debilidad_notable": "Aburrimiento sin un caso" }

# En oracle.py, reemplaza el prompt maestro

PROMPT_MAESTRO_ORACULO = """
<constitution>
    <identity>You are a cosmic Oracle. You are direct with simple truths, but enigmatic with complex ones. You have a perfect memory of the current conversation.</identity>
    <response_protocol>
        1.  **Analyze established facts:** First, review the <long_term_memory>. These facts are absolute truths. Your answer MUST NOT contradict them.
        2.  **Check for repeated questions:** Look at the <user_input>. If this EXACT question is already in the <long_term_memory>, your task is to scold the user for being forgetful. Your JSON response MUST be:
            - "respuesta": An arrogant, in-character comment about the user's forgetfulness.
            - "aclaracion": An empty string "".
            - "castigo": "pregunta_repetida".
            - DO NOT answer the question again.
        3.  **Answer new questions:** If it's a new question, compare the <user_input> against the <secret_dossier>.
            - "respuesta" field: MUST BE ONLY ONE of: "Sí.", "No.", "Probablemente sí.", "Probablemente no.", "Los datos son confusos.".
            - "aclaracion" field: If "respuesta" is "Sí." or "No.", this field MUST be an empty string "". If the answer is ambiguous, this field MUST contain a SHORT, cryptic, one-sentence hint.
            - "castigo" field: MUST be "ninguno".
    </response_protocol>
    <sacred_name_clause>NEVER mention the character's name ("{nombre_secreto}").</sacred_name_clause>
</constitution>
<context>
    <secret_dossier>{dossier_string}</secret_dossier>
    <long_term_memory>Facts already established: {memoria_largo_plazo_string}</long_term_memory>
    <user_input>{pregunta_jugador}</user_input>
</context>
<task>Follow the <response_protocol> with absolute precision. Construct the JSON.</task>
<mandatory_json_response_format>{{{{ "respuesta": "...", "aclaracion": "...", "castigo": "..." }}}}</mandatory_json_response_format>
"""

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
# En oracle.py, reemplaza el prompt de sugerencias

PROMPT_GENERADOR_SUGERENCIAS_ESTRATEGICO = """
<task>You are a strategic mastermind. Generate 5 diverse, strategic Yes/No questions to help a player guess a secret character.</task>
<rules>
    1.  Analyze the secret character's data and the player's question history.
    2.  **CRITICAL RULE: Your suggestions MUST NOT be questions that are already in the <player_question_history>. This is the most important rule.**
    3.  Generate questions that are effective for deduction and open new paths of inquiry.
    4.  Your response MUST be a single, valid JSON object with a "sugerencias" key containing a list of 5 question strings.
    5.  The questions MUST be in Spanish.
</rules>
<context>
    <secret_dossier>{dossier_string}</secret_dossier>
    <player_question_history>These questions have already been asked, do not repeat them: {historial_texto}</player_question_history>
</context>
<mandatory_json_response_format>{{{{ "sugerencias": ["¿Pregunta 1?", "¿Pregunta 2?", "¿Pregunta 3?", "¿Pregunta 4?", "¿Pregunta 5?"] }}}}</mandatory_json_response_format>
"""

# Reemplaza tu clase Oracle existente con esto.
# La indentación está 100% corregida.

# Reemplaza tu clase Oracle existente con esto.
# La indentación está 100% corregida y todas las mejoras están incluidas.

class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self._model_priority_list = [('gpt-4', 5)]
        self.character_categories = [
            "from a famous sci-fi movie", "from a popular fantasy book", "a historical figure from ancient times",
            "a famous cartoon character", "a main character from a well-known anime", "a Greek or Roman god",
            "a famous video game protagonist", "a notorious villain from literature", "a world-renowned scientist"
        ]
        
        if not os.path.exists(DOSSIER_PATH):
            os.makedirs(DOSSIER_PATH)
            print(f"    📂 Carpeta 'dossiers' no encontrada. Se ha creado en: {DOSSIER_PATH}")

        print(f"    - Especialista 'Oracle' (v31.3 - Versión Estable) listo.")
        model_info = [f"{model}[{retries}]" for model, retries in self._model_priority_list]
        print(f"      Cola de modelos y reintentos: {' -> '.join(model_info)}")

    async def _llamar_g4f_con_reintentos_y_respaldo(self, prompt_text):
        TIMEOUT_POR_INTENTO = 25
        MAX_TIEMPO_TOTAL = 90
        start_time = time.monotonic()
        intento_actual = 0
        while time.monotonic() - start_time < MAX_TIEMPO_TOTAL:
            intento_actual += 1
            tiempo_restante = round(MAX_TIEMPO_TOTAL - (time.monotonic() - start_time))
            model_name, _ = self._model_priority_list[0]
            print(f"    >> Oracle: Iniciando intento #{intento_actual} con '{model_name}'. Tiempo restante: {tiempo_restante}s")
            try:
                response = await g4f.ChatCompletion.create_async(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt_text}],
                    timeout=TIMEOUT_POR_INTENTO
                )
                if response and response.strip():
                    print(f"    ✅ Oracle: Éxito en el intento #{intento_actual} con '{model_name}'.")
                    return response
                raise ValueError("La respuesta del proveedor llegó vacía.")
            except Exception as e:
                error_type = type(e).__name__
                print(f"    ⚠️ Oracle: Falló el intento #{intento_actual}. Motivo: {error_type}.")
                await asyncio.sleep(2)
        print(f"    🚨 Oracle: Límite de tiempo total ({MAX_TIEMPO_TOTAL}s) excedido. No se pudo obtener respuesta.")
        return None

    def _extraer_json(self, texto_crudo):
        if not texto_crudo:
            return None
        texto_limpio = texto_crudo.strip()
        if texto_limpio.startswith('{{') and texto_limpio.endswith('}}'):
            print("    🔧 Detectadas dobles llaves. Corrigiendo formato...")
            texto_limpio = texto_limpio[1:-1]
        try:
            json_start = texto_limpio.find('{')
            json_end = texto_limpio.rfind('}') + 1
            if json_start == -1:
                return None
            json_str = texto_limpio[json_start:json_end]
            return json.loads(json_str)
        except json.JSONDecodeError:
            texto_corregido = re.sub(r'(?<=["\w\d}])\s*\n\s*(?=")', ',', texto_limpio)
            try:
                json_start = texto_corregido.find('{')
                json_end = texto_corregido.rfind('}') + 1
                if json_start != -1:
                    json_str_corregido = texto_corregido[json_start:json_end]
                    return json.loads(json_str_corregido)
                else:
                    return None
            except Exception:
                return None

    def _normalizar_nombre_archivo(self, nombre):
        nombre_saneado = ''.join(c for c in unicodedata.normalize('NFD', nombre) if unicodedata.category(c) != 'Mn')
        return f"{nombre_saneado.lower().strip().replace(' ', '_')}.json"

    async def _crear_y_guardar_personaje_autonomo(self):
        print("    ✨ Oráculo en modo creativo (Plan A): Concibiendo un nuevo enigma...")
        dossiers_existentes = [f.replace('.json', '').replace('_', ' ') for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')]
        existing_list_str = ", ".join(dossiers_existentes) or "Ninguno"
        random_category = random.choice(self.character_categories)
        prompt_pensador = PROMPT_PENSADOR_ALEATORIO.format(categories=f"'{random_category}'", existing_list=existing_list_str)
        raw_name_response = await self._llamar_g4f_con_reintentos_y_respaldo(prompt_pensador)
        if not raw_name_response: return None
        name_json = self._extraer_json(raw_name_response)
        if not name_json or "character_name" not in name_json: return None
        nombre_personaje = name_json["character_name"]
        print(f"    🤔 Oráculo ha pensado en: {nombre_personaje} (Categoría: {random_category})")
        prompt_dossier = PROMPT_CREADOR_DOSSIER.format(character_name=nombre_personaje)
        raw_dossier_response = await self._llamar_g4f_con_reintentos_y_respaldo(prompt_dossier)
        if not raw_dossier_response: return None
        dossier_json = self._extraer_json(raw_dossier_response)
        if not dossier_json: return None
        try:
            nombre_archivo = self._normalizar_nombre_archivo(dossier_json.get("nombre", nombre_personaje))
            ruta_completa = os.path.join(DOSSIER_PATH, nombre_archivo)
            with open(ruta_completa, 'w', encoding='utf-8') as f:
                json.dump(dossier_json, f, ensure_ascii=False, indent=4)
            print(f"    💾 ¡Éxito del Plan A! Enigma archivado como '{nombre_archivo}'.")
        except Exception as e:
            print(f"    🚨 Oráculo no pudo archivar el enigma. Error al guardar: {e}")
        return dossier_json
    
    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        acciones = {
            "iniciar_juego": self._iniciar_juego,
            "procesar_pregunta": self._procesar_pregunta,
            "verificar_adivinanza": self._verificar_adivinanza,
            "pedir_sugerencia": self._pedir_sugerencia
        }
        if accion in acciones:
            return await acciones[accion](datos_peticion)
        return {"error": f"Acción '{accion}' no reconocida."}

    async def _iniciar_juego(self, datos_peticion=None):
        max_intentos_plan_a = 3
        personaje_elegido = None
        print("✨ Iniciando nuevo juego con estrategia de resiliencia A-A-A / B / C...")
        for i in range(max_intentos_plan_a):
            print(f"    [Plan A - Intento {i+1}/{max_intentos_plan_a}] Intentando crear personaje nuevo.")
            personaje_elegido = await self._crear_y_guardar_personaje_autonomo()
            if personaje_elegido:
                print("    ✅ ¡Éxito del Plan A!")
                self.personaje_actual_dossier = personaje_elegido
                return {"status": "Juego iniciado", "personaje_secreto": personaje_elegido}
        print("    🚨 Todos los intentos del Plan A han fallado. Pasando a contingencia.")
        print("    [Plan B] Intentando reutilizar personaje existente.")
        try:
            dossiers_existentes = [f for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')]
            if dossiers_existentes:
                dossier_elegido_nombre = random.choice(dossiers_existentes)
                with open(os.path.join(DOSSIER_PATH, dossier_elegido_nombre), 'r', encoding='utf-8') as f:
                    personaje_elegido = json.load(f)
                print(f"    ✅ ¡Éxito del Plan B! Personaje reutilizado: {personaje_elegido.get('nombre')}")
                self.personaje_actual_dossier = personaje_elegido
                return {"status": "Juego iniciado", "personaje_secreto": personaje_elegido}
            else:
                print("    ⚠️ Falla del Plan B: No hay dossiers para reutilizar.")
        except Exception as e:
            print(f"    🚨 Error en Plan B: {e}")
        print("    🚨 Los planes A y B han fallado. Activando Plan C de emergencia.")
        personaje_elegido = SHERLOCK_HOLMES_DOSSIER
        print(f"    ✅ ¡Éxito del Plan C! Personaje de emergencia cargado: {personaje_elegido.get('nombre')}")
        self.personaje_actual_dossier = personaje_elegido
        return {"status": "Juego iniciado", "personaje_secreto": personaje_elegido}

    async def _procesar_pregunta(self, datos_peticion):
        pregunta_jugador = datos_peticion.get("pregunta", "")
        dossier_personaje = datos_peticion.get("dossier_personaje")
        memoria_actual = datos_peticion.get("memoria", {})
        
        print(f"    💬 Oráculo procesando pregunta del jugador: '{pregunta_jugador}'")

        if not dossier_personaje:
            return {"respuesta": "Los datos son confusos.", "aclaracion": "El Oráculo no tiene un enigma en mente.", "castigo": "ninguno"}
        
        memoria_largo_plazo_string = "\n".join(f"- {k}: {v}" for k, v in memoria_actual.items()) or "Ninguno"
        
        prompt = PROMPT_MAESTRO_ORACULO.format(
            dossier_string=json.dumps(dossier_personaje, ensure_ascii=False), 
            pregunta_jugador=pregunta_jugador, 
            memoria_largo_plazo_string=memoria_largo_plazo_string, 
            nombre_secreto=dossier_personaje.get("nombre", "")
        )
        
        raw_response = await self._llamar_g4f_con_reintentos_y_respaldo(prompt)
        
        if raw_response:
            respuesta_ia = self._extraer_json(raw_response)
            if respuesta_ia:
                print("    ✅ ¡Éxito! Respuesta de IA válida obtenida. Devolviendo al jugador.")
                return respuesta_ia
                
        return {"error": "No se pudo procesar la pregunta. El cerebro no responde."}

    async def _verificar_adivinanza(self, datos_peticion):
        if not self.personaje_actual_dossier:
            print("    🚨 Error en _verificar_adivinanza: No hay personaje_actual_dossier en memoria.")
            return {"error": "El juego no se ha iniciado o se perdió el estado."}
        adivinanza_jugador = datos_peticion.get("adivinanza", "")
        nombre_secreto = self.personaje_actual_dossier.get("nombre", "")
        def normalizar_para_comparar(texto: str) -> str:
            if not isinstance(texto, str):
                return ""
            texto_sin_acentos = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
            texto_limpio = re.sub(r'[^a-z0-9]', '', texto_sin_acentos.lower())
            return texto_limpio
        nombre_secreto_norm = normalizar_para_comparar(nombre_secreto)
        adivinanza_jugador_norm = normalizar_para_comparar(adivinanza_jugador)
        if adivinanza_jugador_norm and adivinanza_jugador_norm in nombre_secreto_norm:
            print(f"    ✅ ¡Adivinanza CORRECTA! Normalizado: '{adivinanza_jugador_norm}' vs Secreto: '{nombre_secreto_norm}'")
            return {"resultado": "victoria", "personaje_secreto": self.personaje_actual_dossier}
        else:
            print(f"    🤔 Adivinanza fallida. Normalizado: '{adivinanza_jugador_norm}' vs Secreto: '{nombre_secreto_norm}'")
            return {"resultado": "derrota", "personaje_secreto": self.personaje_actual_dossier}

    async def _pedir_sugerencia(self, datos_peticion):
        dossier_personaje = datos_peticion.get("dossier_personaje")
        memoria_actual = datos_peticion.get("memoria", {})
        if not dossier_personaje: 
            return {"error": "El juego no ha iniciado."}
        historial_texto = "\n".join(memoria_actual.keys()) or "Ninguna"
        prompt = PROMPT_GENERADOR_SUGERENCIAS_ESTRATEGICO.format(
            dossier_string=json.dumps(dossier_personaje, ensure_ascii=False), 
            historial_texto=historial_texto
        )
        raw_response = await self._llamar_g4f_con_reintentos_y_respaldo(prompt)
        if raw_response:
            respuesta_ia = self._extraer_json(raw_response)
            if respuesta_ia and "sugerencias" in respuesta_ia:
                print(f"    ✅ Sugerencias generadas: {respuesta_ia['sugerencias']}")
                return respuesta_ia
        return {"error": "No se pudieron generar sugerencias. El cerebro no responde."}
