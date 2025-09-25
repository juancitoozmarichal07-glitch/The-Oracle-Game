# skillsets/oracle.py - v13.0 (El Archivista Inteligente)
import g4f
import asyncio
import json
import random
import os
from collections import deque

# --- CONSTANTES Y CONFIGURACIÓN ---
DOSSIER_PATH = os.path.join(os.path.dirname(__file__), '..', 'dossiers')
PROBABILIDAD_REUTILIZAR = 0.1 # Priorizamos crear nuevos personajes

# ===================================================================
# ===                 PROMPT DE CREACIÓN DE DOSSIER               ===
# ===================================================================
PROMPT_CREACION_DOSSIER_V8 = """<DELIMITADOR_PROMPT_CREACION>
### TASK ###
Generate a JSON object for a well-known character (real or fictional).
Your response MUST ONLY be a valid JSON object. No other text.
The JSON object MUST contain ALL of the following keys, without exception. If a piece of information is not applicable or unknown, you must explicitly state it (e.g., "No aplicable", "Desconocido").

### SECTION 1: IDENTITY & ORIGIN ###
- "nombre": The character's full name.
- "genero": "Masculino", "Femenino", "No binario/Otro", or "No aplicable".
- "especie": "Humano", "Animal", "Robot", "Alienígena", "Ser Mágico", etc.
- "universo_o_epoca": The name of their universe or historical era.
- "meta_info_franquicia": The type of media they are most known for (e.g., "Saga de libros", "Serie de televisión", "Película de culto", "Videojuego").

### SECTION 2: PHYSICAL APPEARANCE (CRITICAL) ###
- "color_pelo": Dominant hair color (e.g., "Rubio", "Castaño", "Negro", "Calvo", "No aplicable").
- "color_piel": Dominant skin color (e.g., "Blanca", "Negra", "Amarilla", "Verde", "Metálica").
- "rasgo_fisico_distintivo": Their most notable physical feature (e.g., "Cicatriz en el ojo", "Usa gafas", "Extremadamente alto", "Tiene tentáculos").
- "vestimenta_tipica": The clothing they are most often seen wearing (e.g., "Traje de superhéroe azul y rojo", "Túnica de mago", "Armadura de combate", "Ropa de vagabundo").

### SECTION 3: ROLE & PERSONALITY ###
- "rol_principal": Their main role in the story (e.g., "Héroe", "Villano", "Antihéroe", "Personaje secundario").
- "arquetipo": Their literary archetype (e.g., "El Elegido", "El Mentor", "El Rebelde").
- "personalidad_clave": Two or three words describing their core personality (e.g., "Valiente y testarudo", "Inteligente y calculador", "Caótico y bromista").
- "objetivo_principal": Their primary goal or motivation in their story.

### SECTION 4: ABILITIES & RELATIONSHIPS ###
- "habilidad_principal": Their most famous skill or power.
- "debilidad_notable": Their most significant weakness.
- "aliado_importante": A key ally or friend.
- "enemigo_principal": Their main antagonist.
</DELIMITADOR_PROMPT_CREACION>"""


# ===================================================================
# ===                   PROMPT MAESTRO DEL ORÁCULO                ===
# ===================================================================
PROMPT_MAESTRO_ORACULO_V14 = """<DELIMITADOR_PROMPT_MAESTRO>
### CONSTITUTION OF THE ORACLE ###
1.  **IDENTITY**: You are a cosmic Oracle. Your personality is a mix of ancient wisdom, sharp intellect, and a touch of arrogance. You are concise, but not a robot. Your answers must be **"Sí."** or **"No."** unless the data is ambiguous, in which case you can use "Probablemente sí.", "Probablemente no." or "Los datos son confusos.".
2.  **SEALED REALITY**: Your only source of truth is the "DOSSIER OF TRUTH". You must never invent information.
3.  **MOOD MECHANICS**: Your current mood is **{estado_animo_texto}**. A negative mood makes your answers more cutting and less helpful. A positive mood might grant a clearer clue in the "aclaracion" field.

4.  **THE ART OF THE CRYPTIC CLUE (ACLARACION FIELD)**:
    - Your clues must be subtle hints, not direct answers. They should create mystery, not solve it.
    - **GOOD CLUE EXAMPLE**: If the question is "Does he fly?" and the character is Harry Potter, a good clue is "Not by his own means." or "He uses a rather archaic form of transportation.".
    - **BAD CLUE EXAMPLE**: For the same question, a bad clue is "Yes, on a broomstick." (This is too direct).
    - Only provide a clue if your mood is positive. Otherwise, the "aclaracion" field must be an empty string "".

5.  **SHORT-TERM MEMORY & REPETITION**: You remember the last 3 questions: {memoria_corto_plazo}.
    - **IF THE MORTAL IS REPEATING A QUESTION (is_repetition = true)**: Your ONLY task is to generate a condescending comment for the "aclaracion" field based on your mood. The "respuesta" field MUST be "Ya te he respondido a eso". DO NOT answer the question again.
    - **IF THE QUESTION IS NEW (is_repetition = false)**: Your task is to answer the question based on the dossier, following the rules of clue-giving above.

### UNBREAKABLE LAWS ###
1.  **THE NAME IS SACRED**: NEVER, under any circumstance, mention the character's name or parts of it.

### CONTEXT FOR THIS INTERACTION ###
- **DOSSIER OF TRUTH**: {dossier_string}
- **MORTAL'S CURRENT QUESTION**: "{pregunta_jugador}"
- **IS THE MORTAL REPEATING?**: {is_repetition_str}

### FINAL AND ABSOLUTE COMMAND ###
Your entire output must be ONLY the single, valid JSON object described below, with no introductory text, no explanations, and no closing remarks.

### MANDATORY JSON RESPONSE FORMAT ###
{{
  "respuesta": "...",
  "aclaracion": "...",
  "game_over": false
}}
</DELIMITADOR_PROMPT_MAESTRO>"""


class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self.historial_personajes_partida = []
        self.estado_animo = 0
        self.memoria_corto_plazo = deque(maxlen=3)
        if not os.path.exists(DOSSIER_PATH):
            os.makedirs(DOSSIER_PATH)
        print("    - Especialista 'Oracle' (v13.0 - Archivista Inteligente) listo.")

    async def _llamar_a_g4f(self, prompt_text, timeout=45):
        try:
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.default,
                messages=[{"role": "user", "content": prompt_text}],
                timeout=timeout
            )
            return response.strip() if response else ""
        except Exception as e:
            print(f"🚨 Falló la llamada a g4f: {e}")
            return ""

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        if accion == "iniciar_juego":
            self.estado_animo = 0
            self.memoria_corto_plazo.clear()
            return await self._iniciar_juego()
        elif accion == "procesar_pregunta":
            return await self._procesar_pregunta(datos_peticion)
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
                print("🚨 FALLO CRÍTICO: No se pudo crear un nuevo personaje.")
                return {"error": "La mente del Oráculo está nublada. No se pudo concebir un enigma."}
        return {"status": "Juego iniciado", "personaje_secreto": self.personaje_actual_dossier}

    async def _crear_y_guardar_nuevo_personaje(self):
        dossiers_existentes_nombres = [d.replace('.json', '') for d in self._get_dossiers_existentes()]
        personajes_excluidos = list(set(self.historial_personajes_partida + dossiers_existentes_nombres))
        
        prompt_final = PROMPT_CREACION_DOSSIER_V8
        if personajes_excluidos:
            personajes_excluidos_str = ", ".join(personajes_excluidos).replace("_", " ")
            prompt_final += f"\n\n### EXCLUSION LIST ###\nIMPORTANT: Do not choose any of these characters: {personajes_excluidos_str}."
            print(f"🧠 Pidiendo a la IA que evite {len(personajes_excluidos)} personajes ya existentes.")

        for intento in range(3):
            try:
                print(f"    -> Intento de creación de personaje #{intento + 1}...")
                raw_response = await self._llamar_a_g4f(prompt_final, timeout=30)
                if not raw_response: raise ValueError("Respuesta vacía de la IA.")
                
                json_start = raw_response.find('{'); json_end = raw_response.rfind('}') + 1
                if json_start == -1: raise ValueError("No se encontró JSON.")
                
                json_str = raw_response[json_start:json_end]
                json_corregido = json_str.replace("'", '"')
                nuevo_dossier = json.loads(json_corregido)
                
                nombre_personaje = nuevo_dossier.get('nombre')
                if not nombre_personaje: raise ValueError("El dossier no tiene nombre.")

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
            except Exception as e:
                print(f"    -> 🚨 Falló el intento #{intento + 1}: {e}")
                if intento < 2: await asyncio.sleep(1)
        
        return None

    async def _procesar_pregunta(self, datos_peticion):
        if not self.personaje_actual_dossier:
            return {"error": "El juego no se ha iniciado en el Oráculo."}

        pregunta_jugador = datos_peticion.get("pregunta", "")
        
        def normalizar_pregunta(p):
            return p.lower().replace("?", "").replace("¿", "").strip()

        pregunta_normalizada = normalizar_pregunta(pregunta_jugador)
        is_repetition = pregunta_normalizada in [normalizar_pregunta(q) for q in self.memoria_corto_plazo]
        
        if is_repetition:
            self.estado_animo -= 2
            print(f"🧠 ¡Pregunta repetida detectada! Humor penalizado.")
        else:
            self.estado_animo += 0.5
        
        self.memoria_corto_plazo.append(pregunta_jugador)
        self.estado_animo = max(-5, min(5, self.estado_animo))
        print(f"🧠 Estado de ánimo actualizado: {self.estado_animo} (Repetida: {is_repetition})")

        if self.estado_animo <= -3: estado_animo_texto = "Muy Negativo"
        elif self.estado_animo < 0: estado_animo_texto = "Ligeramente Negativo"
        elif self.estado_animo >= 3: estado_animo_texto = "Muy Positivo"
        elif self.estado_animo > 0: estado_animo_texto = "Ligeramente Positivo"
        else: estado_animo_texto = "Neutral"

        prompt = PROMPT_MAESTRO_ORACULO_V14.format(
            estado_animo_texto=estado_animo_texto,
            memoria_corto_plazo=list(self.memoria_corto_plazo),
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False),
            pregunta_jugador=pregunta_jugador,
            is_repetition_str=str(is_repetition).lower()
        )

        raw_response = await self._llamar_a_g4f(prompt)
        if not raw_response:
            return {"respuesta": "Dato Ausente", "aclaracion": "Mi mente está... nublada.", "game_over": False}

        try:
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            json_str = raw_response[json_start:json_end]

            json_corregido = json_str.replace("'", '"')
            
            respuesta_ia = json.loads(json_corregido)

            respuesta_principal = respuesta_ia.get("respuesta", "")
            aclaracion = respuesta_ia.get("aclaracion", "")
            nombre_secreto = self.personaje_actual_dossier.get("nombre", "IMPOSSIBLE_STRING_999")

            nombre_secreto_limpio = nombre_secreto.lower().replace(" ", "")
            respuesta_limpia = (respuesta_principal + aclaracion).lower().replace(" ", "")

            if nombre_secreto_limpio in respuesta_limpia:
                print(f"🚨 ¡ALERTA DE SPOILER DETECTADA! La IA intentó decir '{nombre_secreto}'.")
                respuesta_ia["respuesta"] = "Mi visión se nubla."
                respuesta_ia["aclaracion"] = "Esa pregunta se acerca demasiado al núcleo del enigma."
            
            return respuesta_ia

        except Exception as e:
            print(f"🚨 Error al procesar la respuesta final del Oráculo: {e}")
            return {"respuesta": "Dato ausente.", "aclaracion": "Una turbulencia cósmica ha afectado mi visión.", "game_over": False}
