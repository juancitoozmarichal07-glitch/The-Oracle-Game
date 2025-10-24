# skillsets/oracle.py - v21.0 (Creación Blindada y Anti-Fallo)
import g4f
import asyncio
import json
import random
import os
from collections import deque

# --- CONSTANTES Y CONFIGURACIÓN ---
DOSSIER_PATH = os.path.join(os.path.dirname(__file__), '..', 'dossiers')
PROBABILIDAD_REUTILIZAR = 0.2 # Aumentamos la probabilidad para más variedad

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
# ===                 PROMPTS (CREACIÓN Y PREGUNTA)               ===
# ===================================================================
PROMPT_CREACION_DOSSIER_V9 = """
### TASK ###
Generate a JSON object for a well-known character (real or fictional).

### ABSOLUTE RULES ###
1.  Your response MUST ONLY be a valid JSON object.
2.  DO NOT include any introductory text like "Here is the JSON:".
3.  DO NOT wrap the JSON in markdown backticks (```json).
4.  Your response MUST start with `{` and MUST end with `}`.
5.  The JSON object must contain ALL keys from the template below. If info is unknown, use "Desconocido".

### JSON TEMPLATE ###
- "nombre": The character's full name.
- "genero": "Masculino", "Femenino", "No binario/Otro", or "No aplicable".
- "especie": "Humano", "Animal", "Robot", "Alienígena", "Ser Mágico", etc.
- "universo_o_epoca": The name of their universe or historical era.
- "meta_info_franquicia": The type of media they are most known for (e.g., "Saga de libros", "Serie de televisión", "Película de culto", "Videojuego").
- "rol_principal": Their main role in the story.
- "arquetipo": Their literary archetype.
- "personalidad_clave": Two or three words describing their core personality.
- "habilidad_principal": Their most famous skill or power.
- "debilidad_notable": Their most significant weakness.

### YOUR JSON-ONLY RESPONSE ###
"""

PROMPT_MAESTRO_ORACULO_V21 = """
### CONSTITUTION OF THE ORACLE ###
1.  **IDENTITY**: You are a cosmic Oracle. Your personality is a mix of ancient wisdom, sharp intellect, and a touch of arrogance.
2.  **CORE LOGIC**: You will be given a user's input and must determine the user's INTENT. There are three possible intents: "pregunta_juego", "interaccion_social", "falta_respeto".
3.  **INTENT 1: "pregunta_juego"**:
    - This is a relevant Yes/No question about the secret character.
    - Your "respuesta" MUST be "Sí.", "No.", "Probablemente sí.", "Probablemente no." or "Los datos son confusos.", based on the DOSSIER.
    - Your "castigo" MUST be "ninguno".
    - You can ONLY add a cryptic clue to "aclaracion" if your mood is "Muy Positivo" AND the question is specific and interesting. Otherwise, it MUST be an empty string "".
4.  **INTENT 2: "interaccion_social"**:
    - This is a greeting, a comment, or a question NOT about the character (e.g., "Hola", "Como estas?", "Quien eres?").
    - Your "respuesta" MUST be a short, in-character, philosophical, or condescending comment.
    - Your "castigo" MUST be "social". This tells the game not to count it as a question.
5.  **INTENT 3: "falta_respeto"**:
    - This is any input containing insults, obscenities, or vulgar language.
    - Your "respuesta" MUST be a severe, threatening, in-character warning.
    - Your "castigo" MUST be "penalizacion_grave".
6.  **GAME OVER CLAUSE**: If the user's insolence is repetitive and your mood drops to "Crítico (-5)", your "castigo" MUST become "juego_terminado".
7.  **THE SACRED NAME**: NEVER, under any circumstance, mention the character's name ("{nombre_secreto}") or the franchise ("{franquicia_secreta}"). This is the ultimate rule.

### CONTEXT ###
- **SECRET DOSSIER**: {dossier_string}
- **CURRENT MOOD**: {estado_animo_texto} (from -5 to +5)
- **USER INPUT**: "{pregunta_jugador}"

### YOUR TASK ###
1.  Determine the INTENT.
2.  Formulate the response based on the rules for that intent.
3.  Your entire output MUST be ONLY the single, valid JSON object described below.

### MANDATORY JSON RESPONSE FORMAT ###
{{
  "respuesta": "...",
  "aclaracion": "...",
  "castigo": "..."
}}

### YOUR JSON-ONLY RESPONSE ###
"""


class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self.historial_personajes_partida = []
        self.estado_animo = 0
        self.memoria_corto_plazo = deque(maxlen=3)
        self._model_priority_list = ['gpt-4', 'gpt-3.5-turbo', 'llama3-8b-instruct', 'default']
        if not os.path.exists(DOSSIER_PATH):
            os.makedirs(DOSSIER_PATH)
        print(f"    - Especialista 'Oracle' (v21.0 - Blindado) listo.")
        print(f"      Modelos en cola: {self._model_priority_list}")

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

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        if accion == "iniciar_juego":
            self.estado_animo = 0
            self.memoria_corto_plazo.clear()
            return await self._iniciar_juego()
        elif accion == "procesar_pregunta":
            return await self._procesar_pregunta(datos_peticion)
        elif accion == "pedir_sugerencia":
            return await self._pedir_sugerencia()
        else:
            return {"error": f"Acción '{accion}' no reconocida por el Oráculo."}

    def _get_dossiers_existentes(self):
        return [f for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')] if os.path.exists(DOSSIER_PATH) else []

    async def _iniciar_juego(self):
        dossiers_existentes = self._get_dossiers_existentes()
        personaje_cargado = False

        if dossiers_existentes and random.random() < PROBABILIDAD_REUTILIZAR:
            dossiers_disponibles = [d for d in dossiers_existentes if d.replace('.json', '') not in self.historial_personajes_partida]
            if dossiers_disponibles:
                dossier_elegido = random.choice(dossiers_disponibles)
                try:
                    with open(os.path.join(DOSSIER_PATH, dossier_elegido), 'r', encoding='utf-8') as f:
                        self.personaje_actual_dossier = json.load(f)
                    nombre_personaje = self.personaje_actual_dossier.get("nombre", "Desconocido")
                    print(f"📚 Dossier reutilizado: {nombre_personaje}")
                    self.historial_personajes_partida.append(nombre_personaje)
                    personaje_cargado = True
                except Exception as e:
                    print(f"🚨 Error al leer dossier '{dossier_elegido}': {e}. Creando uno nuevo.")
        
        if not personaje_cargado:
            print("🧠 Creando un nuevo personaje con la IA...")
            nuevo_dossier = await self._crear_y_guardar_nuevo_personaje()
            if nuevo_dossier:
                self.personaje_actual_dossier = nuevo_dossier
            else:
                # ¡NUEVO! Lógica de fallback mejorada
                print("🚨 Fallo crítico al crear personaje. Intentando reutilizar un dossier existente como último recurso.")
                if dossiers_existentes:
                    dossier_elegido = random.choice(dossiers_existentes)
                    try:
                        with open(os.path.join(DOSSIER_PATH, dossier_elegido), 'r', encoding='utf-8') as f:
                            self.personaje_actual_dossier = json.load(f)
                        print(f"📚 Reutilización forzada exitosa: {self.personaje_actual_dossier.get('nombre')}")
                    except Exception as e:
                        print(f"🚨 Fallo en reutilización forzada. Usando personaje de emergencia. Error: {e}")
                        self.personaje_actual_dossier = SHERLOCK_HOLMES_DOSSIER
                else:
                    print("🚨 No hay dossiers para reutilizar. Usando personaje de emergencia.")
                    self.personaje_actual_dossier = SHERLOCK_HOLMES_DOSSIER
        
        return {"status": "Juego iniciado", "personaje_secreto": self.personaje_actual_dossier}

    async def _crear_y_guardar_nuevo_personaje(self):
        personajes_excluidos = list(set(self.historial_personajes_partida + [d.replace('.json', '') for d in self._get_dossiers_existentes()]))
        prompt_final = PROMPT_CREACION_DOSSIER_V9
        if personajes_excluidos:
            prompt_final += f"\n### EXCLUSION LIST ###\nDo not choose any of these characters: {', '.join(personajes_excluidos).replace('_', ' ')}."
        
        for intento in range(3):
            print(f"    -> Intento de creación de personaje #{intento + 1}...")
            raw_response = await self._llamar_a_g4f(prompt_final, timeout=30)
            if not raw_response: continue

            nuevo_dossier = self._extraer_json(raw_response)
            if not nuevo_dossier: continue

            nombre_personaje = nuevo_dossier.get('nombre')
            if not nombre_personaje: continue
            
            nombre_personaje_limpio = nombre_personaje.replace(" ", "_")
            if nombre_personaje_limpio in personajes_excluidos:
                print(f"    -> 🚨 ¡La IA ignoró la exclusión y eligió a {nombre_personaje} de nuevo! Reintentando...")
                continue
            
            nombre_archivo = f"{nombre_personaje_limpio}.json"
            with open(os.path.join(DOSSIER_PATH, nombre_archivo), 'w', encoding='utf-8') as f:
                json.dump(nuevo_dossier, f, ensure_ascii=False, indent=4)
            print(f"💾 ¡Nuevo dossier guardado: {nombre_personaje}!")
            self.historial_personajes_partida.append(nombre_personaje)
            return nuevo_dossier
        
        return None # Devuelve None si los 3 intentos fallan

    async def _procesar_pregunta(self, datos_peticion):
        if not self.personaje_actual_dossier: return {"error": "El juego no se ha iniciado."}
        
        pregunta_jugador = datos_peticion.get("pregunta", "")
        
        def normalizar_pregunta(p): return p.lower().replace("?", "").replace("¿", "").strip()
        pregunta_normalizada = normalizar_pregunta(pregunta_jugador)
        is_repetition = pregunta_normalizada in [normalizar_pregunta(q) for q in self.memoria_corto_plazo]
        
        if is_repetition: self.estado_animo -= 2
        
        self.memoria_corto_plazo.append(pregunta_jugador)
        self.estado_animo = max(-5, min(5, self.estado_animo))
        
        if self.estado_animo <= -5: estado_animo_texto = "Crítico"
        elif self.estado_animo < 0: estado_animo_texto = "Negativo"
        elif self.estado_animo >= 3: estado_animo_texto = "Muy Positivo"
        elif self.estado_animo > 0: estado_animo_texto = "Positivo"
        else: estado_animo_texto = "Neutral"
        
        prompt = PROMPT_MAESTRO_ORACULO_V21.format(
            estado_animo_texto=f"{estado_animo_texto} ({self.estado_animo})",
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False),
            pregunta_jugador=pregunta_jugador,
            nombre_secreto=self.personaje_actual_dossier.get("nombre", ""),
            franquicia_secreta=self.personaje_actual_dossier.get("meta_info_franquicia", "")
        )
        
        raw_response = await self._llamar_a_g4f(prompt)
        if not raw_response: return {"respuesta": "Dato Ausente", "aclaracion": "Mi mente está... nublada.", "castigo": "ninguno"}
        
        respuesta_ia = self._extraer_json(raw_response)
        if not respuesta_ia: return {"respuesta": "Dato Ausente", "aclaracion": "Una turbulencia cósmica ha afectado mi visión.", "castigo": "ninguno"}

        # Lógica de actualización de humor post-respuesta
        castigo = respuesta_ia.get("castigo", "ninguno")
        if castigo == "social": self.estado_animo -= 0.5
        elif castigo == "penalizacion_grave": self.estado_animo -= 3
        elif castigo == "ninguno": self.estado_animo += 0.5
        
        self.estado_animo = max(-5, min(5, self.estado_animo))
        print(f"🧠 Estado de ánimo actualizado: {self.estado_animo} | Castigo: {castigo} | Repetida: {is_repetition}")

        return respuesta_ia

    async def _pedir_sugerencia(self):
        if not self.personaje_actual_dossier: return {"error": "El juego no se ha iniciado."}
        
        historial_texto = "\n".join(list(self.memoria_corto_plazo))
        
        prompt_sugerencia = f"""
### TASK ###
You are a strategic mastermind. Your goal is to generate 5 diverse, strategic Yes/No questions to help a player guess a secret character.

### RULES ###
1.  **Analyze the context:** You will be given the secret character's dossier and the player's question history.
2.  **Strategic Questions:** Your questions should be what a master player would ask next. They must be designed to eliminate large possibilities.
3.  **Avoid Repetition:** DO NOT generate questions that have already been asked or are too similar to those in the history.
4.  **No Spoilers:** DO NOT ask questions that are too specific or reveal the character's identity.
5.  **JSON-ONLY Output:** Your response MUST be a single valid JSON object with a "sugerencias" key containing a list of 5 strings.

### CONTEXT ###
- **SECRET DOSSIER:** {json.dumps(self.personaje_actual_dossier, ensure_ascii=False)}
- **PLAYER'S QUESTION HISTORY:**
{historial_texto}

### YOUR JSON-ONLY RESPONSE ###
"""
        raw_response = await self._llamar_a_g4f(prompt_sugerencia)
        if not raw_response: return {"error": "No se pudieron generar sugerencias."}
        
        respuesta_ia = self._extraer_json(raw_response)
        if not respuesta_ia or "sugerencias" not in respuesta_ia or not isinstance(respuesta_ia["sugerencias"], list):
            print(f"🚨 Error al procesar sugerencias estratégicas: formato de JSON inválido.")
            return {"error": "La IA no generó sugerencias en un formato válido."}
        
        return respuesta_ia
