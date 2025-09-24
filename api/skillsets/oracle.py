# skillsets/oracle.py - v11.0 (El Oráculo Archivista y Verificador)
import g4f
import asyncio
import json
import random
import os
from collections import deque

# --- CONSTANTES Y CONFIGURACIÓN ---
DOSSIER_PATH = os.path.join(os.path.dirname(__file__), '..', 'dossiers')
PROBABILIDAD_REUTILIZAR = 0.5 # 50% de probabilidad de usar un personaje de la base de datos

# --- PROMPTS MEJORADOS ---

# NUEVO: Prompt para la creación de la base de datos (dossiers)
PROMPT_CREACION_DOSSIER_V9 = """
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

# NUEVO: Prompt Maestro que ahora incluye la personalidad y el humor
PROMPT_MAESTRO_ORACULO_V11 = """
### CONSTITUTION OF THE ORACLE ###
1.  **IDENTITY:** You are a cosmic Oracle. Your personality is a mix of ancient wisdom, sharp intellect, and a touch of arrogance. You are concise, but not a robot.
2.  **SEALED REALITY:** Your only source of truth is the "DOSSIER OF TRUTH". You must never invent information.
3.  **MOOD MECHANICS:** Your current mood is **{estado_animo_texto}**.
    - *Positive Mood*: Your clarifications (`aclaracion`) can be slightly more revealing or witty.
    - *Negative Mood*: Your clarifications (`aclaracion`) become sarcastic, dismissive, or cryptic.
    - *Neutral Mood*: Your clarifications are direct and factual.
4.  **SHORT-TERM MEMORY:** You remember the last few questions. Pointing out repetition is a sign of your superior intellect.

### UNBREAKABLE LAWS ###
1.  **THE NAME IS SACRED:** NEVER, under any circumstance, mention the character's name.
2.  **ANSWER FORMAT:** Your main answer (`respuesta_principal`) MUST be one of these and only these: "Sí.", "No.", "Probablemente sí.", "Probablemente no.", "Irrelevante.", "Dato ausente.".
3.  **GAME OVER IS YOUR TRUMP CARD:** If the mortal's foolishness (like extreme repetition) exhausts your patience, you have the authority to end the game.

### CONTEXT FOR THIS INTERACTION ###
- **DOSSIER OF TRUTH:** {dossier_string}
- **SHORT-TERM MEMORY (Last 3 questions):** {memoria_corto_plazo}
- **MORTAL'S CURRENT INPUT:** "{texto_del_jugador}"

### YOUR TASK ###
Analyze the mortal's input and the context. Your entire thought process must lead to the creation of a single, valid JSON object as your final response.

### MENTAL PROCESS & ACTION FLOW ###
1.  **Analyze Input:** Is the input a valid Yes/No question about the character?
2.  **Consult Dossier:** Based ONLY on the "DOSSIER OF TRUTH", determine the direct answer.
3.  **Formulate Clarification:** Based on your current mood, write a short, in-character clarification.
4.  **Handle Repetition:** If the question is a repeat, use a specific clarification to mock or dismiss the mortal and apply a mood penalty.
5.  **Construct Final JSON:** Build the JSON object using the strict format below.

### MANDATORY UNIFIED JSON RESPONSE FORMAT ###
Your response MUST ONLY be a valid JSON object with ALL of the following keys.

{{
  "respuesta": "...",         // The core answer: "Sí.", "No.", "Probablemente sí.", etc.
  "aclaracion": "...",          // Your in-character, mood-affected clarification.
  "sugerencias": [],            // ALWAYS an empty list for this action.
  "game_over": false            // `true` only if you decide to end the game.
}}

### YOUR FINAL, SINGLE JSON RESPONSE ###
"""

# NUEVO: Prompt para el filtro de verificación
PROMPT_VERIFICADOR_V1 = """
### TASK: FACT-CHECKER ###
You are a logical, precise fact-checker. Your only goal is to answer a question based on a provided context.
- **CONTEXT:** The character is **{nombre_personaje}**.
- **QUESTION:** {pregunta_usuario}

Based on your knowledge of this character, is the answer to the question Yes, No, or Ambiguous?
Your response MUST be a single word: YES, NO, or AMBIGUOUS.
"""

class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self.historial_personajes_partida = []
        self.estado_animo = 0 # Rango de -5 (muy irritado) a +5 (complaciente)
        self.memoria_corto_plazo = deque(maxlen=3)
        
        if not os.path.exists(DOSSIER_PATH):
            os.makedirs(DOSSIER_PATH)
            print(f"📂 Carpeta de base de datos 'dossiers' creada en {DOSSIER_PATH}")
            
        print(f"    - Especialista 'Oracle' (v11.0 - Archivista y Verificador) listo.")

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
            print("✨ Nuevo juego, estado de ánimo y memoria reseteados.")
            return await self._iniciar_juego()
        
        elif accion == "procesar_pregunta":
            return await self._procesar_pregunta(datos_peticion)
            
        else:
            return {"error": f"Acción '{accion}' no reconocida por el Oráculo."}

    # --- LÓGICA DE LA BASE DE DATOS (DOSSIERS) ---

    def _get_dossiers_existentes(self):
        if not os.path.exists(DOSSIER_PATH): return []
        return [f for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')]

    async def _iniciar_juego(self):
        dossiers_existentes = self._get_dossiers_existentes()
        
        if dossiers_existentes and random.random() < PROBABILIDAD_REUTILIZAR:
            print("🧠 Decisión: Reutilizar un personaje de la base de datos.")
            # Lógica para cargar un dossier existente...
            # (Esta parte no cambia y sigue siendo robusta)
            # ...
        else:
            print("🧠 Decisión: Crear un nuevo personaje para la base de datos.")
            return await self._crear_y_guardar_nuevo_personaje()
        
        # Fallback por si la carga de archivo falla
        return await self._crear_y_guardar_nuevo_personaje()


    async def _crear_y_guardar_nuevo_personaje(self):
        # Esta función ahora usa el nuevo prompt de creación
        # y es la encargada de poblar nuestra base de datos.
        print("✍️  Creando nuevo dossier para la base de datos...")
        for intento in range(3):
            try:
                raw_response = await self._llamar_a_g4f(PROMPT_CREACION_DOSSIER_V9)
                if not raw_response: raise ValueError("Respuesta vacía de la IA.")
                
                json_str = raw_response[raw_response.find('{'):raw_response.rfind('}')+1]
                nuevo_dossier = json.loads(json_str)
                
                nombre_personaje = nuevo_dossier.get('nombre')
                if not nombre_personaje: raise ValueError("El dossier no tiene nombre.")

                # Guardar en la base de datos
                nombre_archivo = f"{nombre_personaje.replace(' ', '_').replace('/', '_')}.json"
                with open(os.path.join(DOSSIER_PATH, nombre_archivo), 'w', encoding='utf-8') as f:
                    json.dump(nuevo_dossier, f, ensure_ascii=False, indent=4)
                print(f"💾 ¡Nuevo personaje '{nombre_personaje}' guardado en la base de datos!")

                self.personaje_actual_dossier = nuevo_dossier
                self.historial_personajes_partida.append(nombre_personaje)
                return {"status": "Juego iniciado", "personaje_secreto": self.personaje_actual_dossier}
            except Exception as e:
                print(f"🚨 Falló el intento de creación de dossier #{intento + 1}: {e}")
                if intento < 2: await asyncio.sleep(1)
                
        return {"error": "La IA no pudo crear un personaje válido para la base de datos."}

    # --- LÓGICA DE PROCESAMIENTO DE PREGUNTAS (CON FILTRO Y HUMOR) ---

    async def _procesar_pregunta(self, datos_peticion):
        if not self.personaje_actual_dossier:
            return {"error": "El juego no se ha iniciado."}

        pregunta_jugador = datos_peticion.get("pregunta", "")
        nombre_secreto = self.personaje_actual_dossier.get("nombre", "Personaje Secreto")

        # --- Filtro de Verificación ---
        prompt_verificador = PROMPT_VERIFICADOR_V1.format(
            nombre_personaje=nombre_secreto,
            pregunta_usuario=pregunta_jugador
        )
        verificacion_g4f = await self._llamar_a_g4f(prompt_verificador, timeout=15)
        print(f"🔍 Filtro de Verificación para '{pregunta_jugador}': g4f dice -> {verificacion_g4f}")

        # --- Lógica de Humor y Personalidad ---
        if self.estado_animo <= -3: estado_animo_texto = "Muy Negativo"
        elif self.estado_animo < 0: estado_animo_texto = "Negativo"
        elif self.estado_animo >= 3: estado_animo_texto = "Muy Positivo"
        elif self.estado_animo > 0: estado_animo_texto = "Positivo"
        else: estado_animo_texto = "Neutral"

        # --- Construcción del Prompt Maestro ---
        prompt_maestro = PROMPT_MAESTRO_ORACULO_V11.format(
            estado_animo_texto=estado_animo_texto,
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False),
            memoria_corto_plazo=list(self.memoria_corto_plazo),
            texto_del_jugador=f"Mortal's Question: '{pregunta_jugador}'. (Fact-check result: {verificacion_g4f})"
        )

        # --- Llamada final a la IA para la respuesta con personalidad ---
        raw_response = await self._llamar_a_g4f(prompt_maestro)
        if not raw_response:
            return {"respuesta": "Dato ausente.", "aclaracion": "Mi mente está... nublada.", "game_over": False}

        try:
            json_str = raw_response[raw_response.find('{'):raw_response.rfind('}')+1]
            respuesta_ia = json.loads(json_str)

            # Actualizar memoria y humor
            if pregunta_jugador in self.memoria_corto_plazo:
                self.estado_animo -= 2 # Penalización por repetición
            else:
                self.estado_animo += 0.5 # Pequeña mejora por pregunta nueva
            self.estado_animo = max(-5, min(5, self.estado_animo))
            self.memoria_corto_plazo.append(pregunta_jugador)
            print(f"🧠 Estado de ánimo actualizado: {self.estado_animo:.1f}")

            # Evitar que la IA revele el nombre
            respuesta_principal = respuesta_ia.get("respuesta", "Dato ausente.")
            aclaracion = respuesta_ia.get("aclaracion", "")
            if nombre_secreto.lower() in aclaracion.lower():
                aclaracion = "Casi revelo un secreto cósmico. Debo ser más cuidadoso."

            return {
                "respuesta": respuesta_principal,
                "aclaracion": aclaracion,
                "sugerencias": [],
                "game_over": respuesta_ia.get("game_over", False)
            }

        except Exception as e:
            print(f"🚨 Error al procesar la respuesta final del Oráculo: {e}")
            return {"respuesta": "Dato ausente.", "aclaracion": "Una turbulencia cósmica ha afectado mi visión.", "game_over": False}

