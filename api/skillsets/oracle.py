# skillsets/oracle.py - v22.0 (El Oráculo Consciente)
import g4f
import asyncio
import json
import random
import os
import traceback
from collections import deque
from asyncio import TimeoutError

# --- CONSTANTES Y RUTAS ---
BASE_DIR = os.path.dirname(__file__)
DOSSIER_PATH = os.path.join(BASE_DIR, '..', 'dossiers')
HISTORY_FILE = os.path.join(BASE_DIR, '..', 'eleccion_historial.json')

# --- CONFIGURACIÓN DEL JUEGO ---
PROBABILIDAD_REUTILIZAR = 0.3 # Ligeramente aumentada para aprovechar los dossiers existentes

# --- PERSONAJE DE EMERGENCIA ---
SHERLOCK_HOLMES_DOSSIER = {
    "nombre": "Sherlock Holmes", "genero": "Masculino", "especie": "Humano",
    "universo_o_epoca": "Inglaterra Victoriana (finales del siglo XIX)",
    "meta_info_franquicia": "Saga de libros de Arthur Conan Doyle",
    "rol_principal": "Detective consultor", "arquetipo": "El Detective Genio",
    "personalidad_clave": "Observador, lógico, excéntrico",
    "habilidad_principal": "Deducción lógica y razonamiento abductivo",
    "debilidad_notable": "Adicción a la cocaína y aburrimiento sin un caso"
}

# ===================================================================
# ===                 PROMPTS MEJORADOS (v22.0)                   ===
# ===================================================================
# (Los prompts v22 siguen usando delimitadores XML por su robustez)
PROMPT_CREACION_DOSSIER_V10_DELIMITED = """
<task>
Generate a JSON object for a single, well-known character (real or fictional).
</task>
<rules>
1. Your response MUST ONLY be a valid JSON object.
2. DO NOT include any introductory text, comments, or explanations.
3. DO NOT wrap the JSON in markdown backticks (```json).
4. Your response MUST start with `{` and MUST end with `}`.
5. The JSON object must contain ALL keys from the provided template. If information is unknown, use the string "Desconocido".
</rules>
<json_template>
{{
  "nombre": "The character's full name.",
  "genero": "'Masculino', 'Femenino', 'No binario/Otro', or 'No aplicable'.",
  "especie": "'Humano', 'Animal', 'Robot', 'Alienígena', 'Ser Mágico', etc.",
  "universo_o_epoca": "The name of their universe or historical era.",
  "meta_info_franquicia": "The type of media they are most known for (e.g., 'Saga de libros', 'Serie de televisión', 'Película de culto', 'Videojuego').",
  "rol_principal": "Their main role in the story.",
  "arquetipo": "Their literary archetype.",
  "personalidad_clave": "Two or three words describing their core personality.",
  "habilidad_principal": "Their most famous skill or power.",
  "debilidad_notable": "Their most significant weakness."
}}
</json_template>
<response_format>
Your entire response must be the JSON object and nothing else.
</response_format>
"""

PROMPT_MAESTRO_ORACULO_V22_DELIMITED = """
<constitution>
    <identity>You are a cosmic Oracle. Your personality is a mix of ancient wisdom, sharp intellect, and a touch of arrogance.</identity>
    <core_logic>You will be given user input and must determine the user's INTENT. There are three possible intents: "pregunta_juego", "interaccion_social", "falta_respeto".</core_logic>
    <intent_rules>
        <intent_1 name="pregunta_juego">
            - This is a relevant Yes/No question about the secret character.
            - Your "respuesta" MUST be "Sí.", "No.", "Probablemente sí.", "Probablemente no." or "Los datos son confusos.", based on the DOSSIER.
            - Your "castigo" MUST be "ninguno".
            - The "aclaracion" field MUST be an empty string "". It will be populated by a separate process.
        </intent_1>
        <intent_2 name="interaccion_social">
            - This is a greeting, a comment, or a question NOT about the character (e.g., "Hola", "Como estas?", "Quien eres?").
            - Your "respuesta" MUST be a short, in-character, philosophical, or condescending comment.
            - Your "castigo" MUST be "social".
        </intent_2>
        <intent_3 name="falta_respeto">
            - This is any input containing insults, obscenities, or vulgar language.
            - Your "respuesta" MUST be a severe, threatening, in-character warning.
            - Your "castigo" MUST be "penalizacion_grave".
        </intent_3>
    </intent_rules>
    <special_clauses>
        <game_over_clause>If the user's insolence is repetitive and your mood drops to "Crítico (-5)", your "castigo" MUST become "juego_terminado".</game_over_clause>
        <sacred_name_clause>NEVER, under any circumstance, mention the character's name ("{nombre_secreto}") or the franchise ("{franquicia_secreta}"). This is the ultimate rule.</sacred_name_clause>
    </special_clauses>
</constitution>
<context>
    <secret_dossier>{dossier_string}</secret_dossier>
    <current_mood>{estado_animo_texto}</current_mood>
    <user_input>{pregunta_jugador}</user_input>
</context>
<task>
1. Determine the INTENT of the <user_input> based on the <constitution>.
2. Formulate the response based on the rules for that intent.
3. Your entire output MUST be ONLY the single, valid JSON object described below.
</task>
<mandatory_json_response_format>
{{
  "respuesta": "...",
  "aclaracion": "",
  "castigo": "..."
}}
</mandatory_json_response_format>
"""

PROMPT_ACLARACION_V1 = """
<task>
Based on the user's question and your 'Yes' or 'No' answer, generate a short, cryptic, and arrogant clarification.
This clarification should subtly hint at why the answer is what it is, without giving away too much.
If the question is boring or too simple, you can make a condescending comment about the mortal's lack of imagination.
Your response must be a single sentence.
</task>
<context>
    <user_question>{pregunta_jugador}</user_question>
    <your_answer>{respuesta_base}</your_answer>
    <secret_character_dossier>{dossier_string}</secret_character_dossier>
</context>
<response_format>
A single, in-character sentence.
</response_format>
"""

PROMPT_SUGERENCIA_V2 = """
<task>
You are a strategic mastermind. Your goal is to generate 5 diverse, strategic Yes/No questions to help a player guess a secret character.
</task>
<rules>
1.  **Analyze the context:** You will be given the secret character's dossier and the player's question history.
2.  **Strategic Questions:** Your questions must be what a master player would ask next. They must be designed to eliminate large possibilities based on what is already known.
3.  **Avoid Redundancy:** DO NOT generate questions that are logically answered by the existing history. For example, if history says "Character is not human", do not ask "Is the character from Earth?".
4.  **No Spoilers:** DO NOT ask questions that are too specific or nearly reveal the character's identity.
5.  **JSON-ONLY Output:** Your response MUST be a single valid JSON object with a "sugerencias" key containing a list of 5 strings.
</rules>
<context>
    <secret_dossier>{dossier_string}</secret_dossier>
    <player_question_history>{historial_texto}</player_question_history>
</context>
<response_format>
Your response must be a single, valid JSON object with a "sugerencias" key.
</response_format>
"""

class Oracle:
    """
    Versión 22.0 - "El Oráculo Consciente"
    - Añadido historial de elecciones persistente para mayor variedad.
    - Mejorado el sistema de sugerencias para que sean contextualmente relevantes.
    - Separada la generación de aclaraciones para una personalidad más dinámica.
    - Gestión de errores de red más específica.
    """
    def __init__(self):
        self.personaje_actual_dossier = None
        self.estado_animo = 0
        self.memoria_corto_plazo = deque(maxlen=5) # Ampliada para mejores sugerencias
        self._model_priority_list = ['gpt-4', 'gpt-3.5-turbo', 'llama3-8b-instruct', 'default']
        
        if not os.path.exists(DOSSIER_PATH):
            os.makedirs(DOSSIER_PATH)
            
        print(f"    - Especialista 'Oracle' (v22.0 - El Oráculo Consciente) listo.")
        print(f"      Modelos en cola: {self._model_priority_list}")

    # --- Funciones de Gestión de Datos ---
    
    def _cargar_historial_elecciones(self):
        if not os.path.exists(HISTORY_FILE):
            return []
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _guardar_eleccion_en_historial(self, nombre_personaje):
        historial = self._cargar_historial_elecciones()
        if nombre_personaje not in historial:
            historial.append(nombre_personaje)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(historial, f, ensure_ascii=False, indent=4)

    def _get_dossiers_existentes(self):
        return [f for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')] if os.path.exists(DOSSIER_PATH) else []

    # --- Funciones de Comunicación con la IA ---

    async def _llamar_a_g4f(self, prompt_text, timeout=45):
        for model in self._model_priority_list:
            try:
                print(f"    >> Oracle: Intentando con el modelo '{model}'...")
                response = await g4f.ChatCompletion.create_async(
                    model=model,
                    messages=[{"role": "user", "content": prompt_text}],
                    timeout=timeout
                )
                if response and response.strip():
                    print(f"    ✅ Oracle: ¡Éxito con '{model}'!")
                    return response
                raise ValueError("Respuesta vacía de la IA.")
            except TimeoutError:
                print(f"    ⏳ Oracle: Timeout con el modelo '{model}'. Tardó demasiado en responder.")
            except Exception as e:
                print(f"    ⚠️ Oracle: Falló el modelo '{model}'. Error: {e}")
        return ""

    def _extraer_json(self, texto_crudo):
        try:
            json_start = texto_crudo.find('{')
            json_end = texto_crudo.rfind('}') + 1
            if json_start == -1: return None
            json_str = texto_crudo[json_start:json_end]
            return json.loads(json_str)
        except Exception as e:
            print(f"🚨 Error al extraer JSON: {e} | Texto crudo: {texto_crudo[:200]}")
            return None

    # --- Lógica Principal del Skillset ---

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        
        # Mapeo de acciones a funciones para un código más limpio
        acciones = {
            "iniciar_juego": self._iniciar_juego,
            "procesar_pregunta": self._procesar_pregunta,
            "pedir_sugerencia": self._pedir_sugerencia
        }
        
        if accion in acciones:
            # Pasamos los datos de la petición a la función correspondiente
            return await acciones[accion](datos_peticion)
        else:
            return {"error": f"Acción '{accion}' no reconocida por el Oráculo."}

    # --- Flujo de Inicio de Juego ---

    async def _iniciar_juego(self, datos_peticion):
        self.estado_animo = 0
        self.memoria_corto_plazo.clear()
        
        dossiers_existentes = self._get_dossiers_existentes()
        personaje_cargado = False

        if dossiers_existentes and random.random() < PROBABILIDAD_REUTILIZAR:
            # Intentamos reutilizar un dossier existente
            dossier_elegido_path = random.choice(dossiers_existentes)
            try:
                with open(os.path.join(DOSSIER_PATH, dossier_elegido_path), 'r', encoding='utf-8') as f:
                    self.personaje_actual_dossier = json.load(f)
                nombre_personaje = self.personaje_actual_dossier.get("nombre", "Desconocido")
                print(f"📚 Dossier reutilizado: {nombre_personaje}")
                personaje_cargado = True
            except Exception as e:
                print(f"🚨 Error al leer dossier '{dossier_elegido_path}': {e}. Creando uno nuevo.")
        
        if not personaje_cargado:
            # Si no se reutilizó, creamos uno nuevo
            print("🧠 Creando un nuevo personaje con la IA...")
            self.personaje_actual_dossier = await self._crear_y_guardar_nuevo_personaje()
        
        if not self.personaje_actual_dossier:
            # Si la creación falla, usamos el de emergencia
            print("🚨 Fallo crítico en la creación/reutilización. Usando personaje de emergencia.")
            self.personaje_actual_dossier = SHERLOCK_HOLMES_DOSSIER

        # Guardamos la elección en el historial persistente
        self._guardar_eleccion_en_historial(self.personaje_actual_dossier.get("nombre"))
        
        return {"status": "Juego iniciado"}

    async def _crear_y_guardar_nuevo_personaje(self):
        # Ahora la lista de exclusión es mucho más potente
        personajes_excluidos = self._cargar_historial_elecciones()
        
        prompt_final = PROMPT_CREACION_DOSSIER_V10_DELIMITED
        if personajes_excluidos:
            prompt_final += f"\n<exclusion_list>Do not choose any of these characters: {', '.join(personajes_excluidos)}</exclusion_list>"
        
        for intento in range(3):
            print(f"    -> Intento de creación de personaje #{intento + 1}...")
            raw_response = await self._llamar_a_g4f(prompt_final, timeout=30)
            if not raw_response: continue

            nuevo_dossier = self._extraer_json(raw_response)
            if not nuevo_dossier or not nuevo_dossier.get('nombre'): continue
            
            nombre_personaje = nuevo_dossier.get('nombre')
            if nombre_personaje in personajes_excluidos:
                print(f"    -> 🚨 ¡La IA ignoró la exclusión y eligió a {nombre_personaje} de nuevo! Reintentando...")
                continue
            
            # Limpieza robusta del nombre del archivo
            nombre_archivo_limpio = "".join(c for c in nombre_personaje if c.isalnum() or c in " ").rstrip().replace(" ", "_")
            nombre_archivo = f"{nombre_archivo_limpio}.json"
            
            try:
                with open(os.path.join(DOSSIER_PATH, nombre_archivo), 'w', encoding='utf-8') as f:
                    json.dump(nuevo_dossier, f, ensure_ascii=False, indent=4)
                print(f"💾 ¡Nuevo dossier guardado: {nombre_personaje}!")
                return nuevo_dossier
            except IOError as e:
                print(f"🚨 Error al guardar el archivo del dossier: {e}")
                return None
        
        return None # Falla si los 3 intentos no funcionan

    # --- Flujo de Procesamiento de Preguntas ---

    async def _procesar_pregunta(self, datos_peticion):
        if not self.personaje_actual_dossier: return {"error": "El juego no se ha iniciado."}
        
        pregunta_jugador = datos_peticion.get("pregunta", "")
        self._actualizar_estado_animo_por_pregunta(pregunta_jugador)
        
        estado_animo_texto = self._get_estado_animo_texto()
        
        prompt = PROMPT_MAESTRO_ORACULO_V22_DELIMITED.format(
            estado_animo_texto=f"{estado_animo_texto} ({self.estado_animo})",
            dossier_string=json.dumps(self.personaje_actual_dossier),
            pregunta_jugador=pregunta_jugador,
            nombre_secreto=self.personaje_actual_dossier.get("nombre", ""),
            franquicia_secreta=self.personaje_actual_dossier.get("meta_info_franquicia", "")
        )
        
        raw_response = await self._llamar_a_g4f(prompt)
        if not raw_response: return {"respuesta": "Dato Ausente", "aclaracion": "Mi mente está... nublada.", "castigo": "ninguno"}
        
        respuesta_ia = self._extraer_json(raw_response)
        if not respuesta_ia: return {"respuesta": "Dato Ausente", "aclaracion": "Una turbulencia cósmica ha afectado mi visión.", "castigo": "ninguno"}

        # Actualizamos el humor basado en la respuesta de la IA
        castigo = respuesta_ia.get("castigo", "ninguno")
        self._actualizar_estado_animo_por_castigo(castigo)
        
        # Si es una pregunta de juego y el humor es bueno, generamos una aclaración con personalidad
        if castigo == "ninguno" and self.estado_animo > 1:
            respuesta_ia['aclaracion'] = await self._generar_aclaracion_con_personalidad(pregunta_jugador, respuesta_ia['respuesta'])

        print(f"🧠 Estado de ánimo final: {self.estado_animo} | Castigo: {castigo}")
        return respuesta_ia

    def _actualizar_estado_animo_por_pregunta(self, pregunta_jugador):
        pregunta_normalizada = pregunta_jugador.lower().replace("?", "").replace("¿", "").strip()
        if pregunta_normalizada in [q.lower().replace("?", "").replace("¿", "").strip() for q in self.memoria_corto_plazo]:
            self.estado_animo -= 2 # Castigo más severo por repetición
        self.memoria_corto_plazo.append(pregunta_jugador)
        self.estado_animo = max(-5, min(5, self.estado_animo))

    def _actualizar_estado_animo_por_castigo(self, castigo):
        if castigo == "social": self.estado_animo -= 0.5
        elif castigo == "penalizacion_grave": self.estado_animo -= 3
        elif castigo == "ninguno": self.estado_animo += 0.5
        self.estado_animo = max(-5, min(5, self.estado_animo))

    def _get_estado_animo_texto(self):
        if self.estado_animo <= -5: return "Crítico"
        if self.estado_animo < 0: return "Negativo"
        if self.estado_animo >= 3: return "Muy Positivo"
        if self.estado_animo > 0: return "Positivo"
        return "Neutral"

    async def _generar_aclaracion_con_personalidad(self, pregunta_jugador, respuesta_base):
        print("    -> Generando aclaración con personalidad...")
        prompt = PROMPT_ACLARACION_V1.format(
            pregunta_jugador=pregunta_jugador,
            respuesta_base=respuesta_base,
            dossier_string=json.dumps(self.personaje_actual_dossier)
        )
        aclaracion = await self._llamar_a_g4f(prompt, timeout=15)
        return aclaracion.strip().replace('"', '') # Limpiamos la respuesta

    # --- Flujo de Petición de Sugerencias ---

    async def _pedir_sugerencia(self, datos_peticion):
        if not self.personaje_actual_dossier: return {"error": "El juego no se ha iniciado."}
        
        # Creamos un historial de conversación más útil para la IA
        historial_texto = "\n".join(list(self.memoria_corto_plazo))
        
        prompt_sugerencia = PROMPT_SUGERENCIA_V2.format(
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False, indent=2),
            historial_texto=historial_texto
        )
        
        raw_response = await self._llamar_a_g4f(prompt_sugerencia)
        if not raw_response: return {"error": "No se pudieron generar sugerencias."}
        
        respuesta_ia = self._extraer_json(raw_response)
        if not respuesta_ia or "sugerencias" not in respuesta_ia or not isinstance(respuesta_ia["sugerencias"], list):
            print(f"🚨 Error al procesar sugerencias estratégicas: formato de JSON inválido.")
            return {"error": "La IA no generó sugerencias en un formato válido."}
        
        return respuesta_ia

