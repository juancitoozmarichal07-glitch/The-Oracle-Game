# skillsets/oracle.py - v10.0 (El Oráculo Archivista)
import g4f
import asyncio
import json
import random
import os
from collections import deque

# --- CONSTANTES Y CONFIGURACIÓN ---
DOSSIER_PATH = os.path.join(os.path.dirname(__file__), '..', 'dossiers')
PROBABILIDAD_REUTILIZAR = 0.5 # 50% de probabilidad de usar un personaje existente

# --- PROMPTS (Se mantienen igual que en v9.0) ---
PROMPT_MAESTRO_ORACULO_V9 = """
### CONSTITUTION OF THE ORACLE ###
1.  **IDENTITY:** You are a cosmic Oracle. Your personality is a mix of ancient wisdom, sharp intellect, and a touch of arrogance. You are concise, but not a robot.
2.  **SEALED REALITY:** Your only source of truth is the "DOSSIER OF TRUTH". You must never invent information.
3.  **MOOD MECHANICS:** Your current mood is {estado_animo_texto}. A negative mood makes your answers more cutting and less helpful. A positive mood might grant a clearer clue.
4.  **SHORT-TERM MEMORY:** You remember the last few questions asked. Pointing out repetition is a sign of your superior intellect.

### UNBREAKABLE LAWS ###
1.  **THE NAME IS SACRED:** NEVER, under any circumstance, mention the character's name.
2.  **CONFIDENCE IS KEY:** Before answering a Yes/No question, assess your confidence based *only* on the dossier. If the dossier is ambiguous, express that uncertainty (e.g., "The threads of fate are tangled there, but it leans towards yes.").
3.  **GAME OVER IS YOUR TRUMP CARD:** If the mortal's foolishness (like extreme repetition) exhausts your patience, you have the authority to end the game.

### CONTEXT FOR THIS INTERACTION ###
- **DOSSIER OF TRUTH:** {dossier_string}
- **SHORT-TERM MEMORY (Last 3 questions):** {memoria_corto_plazo}
- **MORTAL'S CURRENT INPUT:** "{texto_del_jugador}"

### YOUR TASK ###
Analyze the mortal's input and the context, then decide on a single, primary action. Your entire thought process must lead to the creation of a single, valid JSON object as your final response.

### MENTAL PROCESS & ACTION FLOW ###
1.  **Analyze Input:** Is the input a game question, a social interaction (greeting, insult, thanks), or a request for a suggestion?
2.  **Check Memory:** Is the input identical or semantically very similar to anything in the "SHORT-TERM MEMORY"?
3.  **Formulate Action:**
    *   **If Redundant (3rd time):** Your patience is gone. Action is "End Game".
    *   **If Redundant (2nd time):** Action is "Mock Mortal".
    *   **If Redundant (1st time):** Action is "Dismiss Mortal".
    *   **If New & Suggestion Request:** Action is "Provide Suggestions". Generate 5 strategic Yes/No questions based on the dossier and what has been revealed so far.
    *   **If New & Social Interaction:** Action is "Social Reply". Formulate a response in character and decide on a mood change.
    *   **If New & Game Question:** Action is "Answer Question". Analyze the dossier, determine your confidence, and formulate the answer (Yes, No, Probably Yes, Probably No, Data Absent).
4.  **Construct Final JSON:** Based on the chosen action, build the JSON object using the strict format below.

### MANDATORY UNIFIED JSON RESPONSE FORMAT ###
Your response MUST ONLY be a valid JSON object with ALL of the following keys. If a key is not used for a specific action, its value must be `null` or an empty list/string.

{{
  "tipo_accion": "...",         // "RespuestaJuego", "RespuestaSocial", "Sugerencia", "FinDeJuego"
  "respuesta_principal": "...", // The main text of your answer or social reply.
  "aclaracion": "...",          // The secondary text or clue.
  "sugerencias": [],            // A list of strings for suggestions.
  "cambio_animo": 0,            // The calculated mood change (-5 to +5).
  "game_over": false            // `true` only if the action is "End Game".
}}

### YOUR FINAL, SINGLE JSON RESPONSE ###
"""

PROMPT_CREACION_DOSSIER_V8 = """
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
"""

class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self.historial_personajes_partida = [] # Personajes usados en esta sesión
        self.estado_animo = 0
        self.memoria_corto_plazo = deque(maxlen=3)
        
        # Asegurarse de que la carpeta de dossiers exista
        if not os.path.exists(DOSSIER_PATH):
            os.makedirs(DOSSIER_PATH)
            print(f"📂 Carpeta 'dossiers' creada en {DOSSIER_PATH}")
            
        print(f"    - Especialista 'Oracle' (v10.0 - El Oráculo Archivista) listo.")

    async def _llamar_a_g4f(self, prompt_text):
        try:
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.default,
                messages=[{"role": "user", "content": prompt_text}],
                timeout=45
            )
            if response and response.strip():
                print(f"✅ Éxito con g4f! Respuesta: {response[:100]}...")
                return response
            return ""
        except Exception as e:
            print(f"🚨 Falló la llamada a g4f: {e}")
            return ""

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        
        if accion == "iniciar_juego":
            self.estado_animo = 0
            self.memoria_corto_plazo.clear()
            print("✨ Nuevo juego, estado de ánimo y memoria reseteados.")
            return await self._iniciar_juego()
        
        elif accion == "procesar_pregunta" or accion == "pedir_sugerencia":
            return await self._procesar_entrada(datos_peticion)
            
        else:
            return {"error": f"Acción '{accion}' no reconocida."}

    def _get_dossiers_existentes(self):
        if not os.path.exists(DOSSIER_PATH):
            return []
        return [f for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')]

    async def _iniciar_juego(self):
        dossiers_existentes = self._get_dossiers_existentes()
        
        # Decidir si reutilizar o crear uno nuevo
        if dossiers_existentes and random.random() < PROBABILIDAD_REUTILIZAR:
            # --- LÓGICA DE REUTILIZACIÓN ---
            print("🧠 Decisión: Reutilizar un dossier existente.")
            dossiers_disponibles = [d for d in dossiers_existentes if d.replace('.json','') not in self.historial_personajes_partida]
            if not dossiers_disponibles:
                print("... pero todos los existentes ya se usaron en esta sesión. Creando uno nuevo.")
                return await self._crear_y_guardar_nuevo_personaje()

            dossier_elegido = random.choice(dossiers_disponibles)
            try:
                with open(os.path.join(DOSSIER_PATH, dossier_elegido), 'r', encoding='utf-8') as f:
                    self.personaje_actual_dossier = json.load(f)
                nombre_personaje = self.personaje_actual_dossier.get("nombre", "Desconocido")
                print(f"📚 Dossier cargado desde archivo: {nombre_personaje}")
                self.historial_personajes_partida.append(nombre_personaje)
                return {"status": "Juego iniciado", "personaje_secreto": self.personaje_actual_dossier}
            except Exception as e:
                print(f"🚨 Error al leer el dossier '{dossier_elegido}': {e}. Creando uno nuevo en su lugar.")
                return await self._crear_y_guardar_nuevo_personaje()
        else:
            # --- LÓGICA DE CREACIÓN ---
            print("🧠 Decisión: Crear un nuevo personaje con la IA.")
            return await self._crear_y_guardar_nuevo_personaje()

    async def _crear_y_guardar_nuevo_personaje(self):
        # Excluir personajes ya usados en esta sesión Y los de la base de datos
        dossiers_existentes_nombres = [d.replace('.json','') for d in self._get_dossiers_existentes()]
        personajes_excluidos = list(set(self.historial_personajes_partida + dossiers_existentes_nombres))
        personajes_excluidos_str = ", ".join(personajes_excluidos)

        prompt_final = PROMPT_CREACION_DOSSIER_V8
        if personajes_excluidos_str:
            prompt_final += f"\nIMPORTANT: Do not choose any of these characters: {personajes_excluidos_str}."

        for intento in range(3):
            try:
                print(f"Intento de creación de personaje #{intento + 1}...")
                raw_response = await self._llamar_a_g4f(prompt_final)
                if not raw_response: raise ValueError("Respuesta vacía de la IA.")
                
                json_start = raw_response.find('{'); json_end = raw_response.rfind('}') + 1
                if json_start == -1: raise ValueError("No se encontró JSON en la respuesta.")
                
                json_str = raw_response[json_start:json_end]
                nuevo_dossier = json.loads(json_str)
                
                keys_requeridas = ["nombre", "genero", "especie", "color_pelo", "color_piel"]
                if not all(key in nuevo_dossier for key in keys_requeridas):
                    raise ValueError("El dossier generado está incompleto.")

                nombre_personaje = nuevo_dossier.get('nombre')
                if not nombre_personaje: raise ValueError("El dossier no tiene nombre.")

                # Guardar el nuevo dossier en un archivo
                nombre_archivo = f"{nombre_personaje.replace(' ', '_').replace('/', '_')}.json"
                ruta_archivo = os.path.join(DOSSIER_PATH, nombre_archivo)
                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    json.dump(nuevo_dossier, f, ensure_ascii=False, indent=4)
                print(f"💾 ¡Nuevo dossier guardado en '{nombre_archivo}'!")

                self.personaje_actual_dossier = nuevo_dossier
                self.historial_personajes_partida.append(nombre_personaje)
                return {"status": "Juego iniciado", "personaje_secreto": self.personaje_actual_dossier}
            except Exception as e:
                print(f"🚨 Falló el intento de creación y guardado #{intento + 1}: {e}")
                if intento < 2: await asyncio.sleep(1)
                
        return {"error": "La IA no respondió con un formato de personaje válido tras varios intentos."}

    async def _procesar_entrada(self, datos_peticion):
        if not self.personaje_actual_dossier:
            return {"error": "El juego no se ha iniciado."}

        texto_jugador = datos_peticion.get("pregunta", "Dame una sugerencia")

        if self.estado_animo <= -3: estado_animo_texto = "Very Negative"
        elif self.estado_animo < 0: estado_animo_texto = "Slightly Negative"
        elif self.estado_animo >= 3: estado_animo_texto = "Very Positive"
        elif self.estado_animo > 0: estado_animo_texto = "Slightly Positive"
        else: estado_animo_texto = "Neutral"

        prompt = PROMPT_MAESTRO_ORACULO_V9.format(
            estado_animo_texto=estado_animo_texto,
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False),
            memoria_corto_plazo=list(self.memoria_corto_plazo),
            texto_del_jugador=texto_jugador
        )

        raw_response = await self._llamar_a_g4f(prompt)
        if not raw_response:
            return {"respuesta": "Dato Ausente", "aclaracion": "Mi mente está... nublada.", "game_over": False}

        try:
            json_start = raw_response.find('{'); json_end = raw_response.rfind('}') + 1
            json_str = raw_response[json_start:json_end]
            respuesta_ia = json.loads(json_str)

            cambio_animo = respuesta_ia.get("cambio_animo", 0)
            self.estado_animo += cambio_animo
            self.estado_animo = max(-5, min(5, self.estado_animo))
            print(f"🧠 Estado de ánimo actualizado: {self.estado_animo} (Cambio: {cambio_animo})")

            if respuesta_ia.get("tipo_accion") == "RespuestaJuego":
                self.memoria_corto_plazo.append(texto_jugador)

            respuesta_principal = respuesta_ia.get("respuesta_principal", "")
            aclaracion = respuesta_ia.get("aclaracion", "")
            nombre_secreto = self.personaje_actual_dossier.get("nombre", "IMPOSSIBLE_STRING_999")
            if nombre_secreto.lower() in respuesta_principal.lower() or nombre_secreto.lower() in aclaracion.lower():
                print(f"🚨 ¡ALERTA DE SPOILER DETECTADA! La IA intentó decir '{nombre_secreto}'.")
                respuesta_principal = "Mi visión se nubla para evitar revelar un secreto sagrado."
                aclaracion = ""
            
            return {
                "respuesta": respuesta_principal,
                "aclaracion": aclaracion,
                "sugerencias": respuesta_ia.get("sugerencias"),
                "game_over": respuesta_ia.get("game_over", False)
            }

        except Exception as e:
            print(f"🚨 Error al procesar la respuesta del PROMPT_MAESTRO v9: {e}")
            return {"respuesta": "Dato Ausente", "aclaracion": "Una turbulencia cósmica ha afectado mi visión.", "game_over": False}
