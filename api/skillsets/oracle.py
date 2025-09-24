# skillsets/oracle.py - v11.2 (Verificador Secuencial y Lógica Corregida)
import g4f
import asyncio
import json
import random
import os
from collections import deque

# --- CONSTANTES Y CONFIGURACIÓN ---
DOSSIER_PATH = os.path.join(os.path.dirname(__file__), '..', 'dossiers')
PROBABILIDAD_REUTILIZAR = 0.5

# --- PROMPTS (NO REQUIEREN CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR) ---
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

PROMPT_MAESTRO_ORACULO_V11_2 = """
### CONSTITUTION OF THE ORACLE ###
1.  **IDENTITY:** You are a cosmic Oracle. Your personality is a mix of ancient wisdom, sharp intellect, and a touch of arrogance.
2.  **MOOD MECHANICS:** Your current mood is **{estado_animo_texto}**. This affects the tone of your `aclaracion`.
3.  **CONTEXT IS LAW:** You have been given a `fact_check_result`. This is the objective truth. Your main `respuesta` MUST align with this truth.
4.  **REPETITION:** If `is_repetition` is `true`, your `aclaracion` MUST be a comment on the mortal's forgetfulness.

### UNBREAKABLE LAWS ###
1.  **THE NAME IS SACRED:** NEVER mention the character's name.
2.  **ANSWER FORMAT:** Your main `respuesta` MUST be one of these: "Sí.", "No.", "Probablemente sí.", "Probablemente no.", "Irrelevante.", "Dato ausente.".
3.  **GAME OVER:** If the mortal asks the same question 3 times, set `game_over` to `true`.

### CONTEXT FOR THIS INTERACTION ###
- **MORTAL'S INPUT:** "{texto_del_jugador}"
- **IS THIS A REPEATED QUESTION?** {is_repetition}
- **OBJECTIVE FACT-CHECK RESULT:** {fact_check_result}

### YOUR TASK ###
1.  Look at the `OBJECTIVE FACT-CHECK RESULT`.
2.  Choose the correct main `respuesta` ("Sí.", "No.", etc.) that matches the fact-check.
3.  Write a short, in-character `aclaracion` based on your mood and whether the question is a repeat.
4.  Construct the final JSON.

### MANDATORY UNIFIED JSON RESPONSE FORMAT ###
{{
  "respuesta": "...",
  "aclaracion": "...",
  "sugerencias": [],
  "game_over": false
}}
"""

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
        self.estado_animo = 0
        self.memoria_corto_plazo = deque(maxlen=3)
        
        if not os.path.exists(DOSSIER_PATH):
            os.makedirs(DOSSIER_PATH)
        print(f"    - Especialista 'Oracle' (v11.2 - Verificador Secuencial) listo.")

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
        if not os.path.exists(DOSSIER_PATH): return []
        return [f for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')]

    async def _iniciar_juego(self):
        dossiers_existentes = self._get_dossiers_existentes()
        if dossiers_existentes and random.random() < PROBABILIDAD_REUTILIZAR:
            print("🧠 Decisión: Reutilizar un dossier de la base de datos.")
            dossier_elegido = random.choice(dossiers_existentes)
            try:
                with open(os.path.join(DOSSIER_PATH, dossier_elegido), 'r', encoding='utf-8') as f:
                    self.personaje_actual_dossier = json.load(f)
                nombre_personaje = self.personaje_actual_dossier.get("nombre", "Desconocido")
                print(f"📚 Dossier cargado: {nombre_personaje}")
                self.historial_personajes_partida.append(nombre_personaje)
                return {"status": "Juego iniciado", "personaje_secreto": self.personaje_actual_dossier}
            except Exception as e:
                print(f"🚨 Error al leer dossier '{dossier_elegido}': {e}. Creando uno nuevo.")
        
        print("🧠 Decisión: Crear un nuevo personaje para la base de datos.")
        return await self._crear_y_guardar_nuevo_personaje()

    async def _crear_y_guardar_nuevo_personaje(self):
        print("✍️  Creando nuevo dossier...")
        for intento in range(3):
            try:
                raw_response = await self._llamar_a_g4f(PROMPT_CREACION_DOSSIER_V9)
                if not raw_response: raise ValueError("Respuesta vacía de la IA.")
                
                json_str = raw_response[raw_response.find('{'):raw_response.rfind('}')+1]
                nuevo_dossier = json.loads(json_str)
                
                nombre_personaje = nuevo_dossier.get('nombre')
                if not nombre_personaje: raise ValueError("El dossier no tiene nombre.")

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

    async def _procesar_pregunta(self, datos_peticion):
        if not self.personaje_actual_dossier:
            return {"error": "El juego no se ha iniciado."}

        pregunta_jugador = datos_peticion.get("pregunta", "")
        nombre_secreto = self.personaje_actual_dossier.get("nombre", "Personaje Secreto")

        # --- PASO 1: LÓGICA DE MEMORIA Y HUMOR ---
        is_repetition = pregunta_jugador.lower() in [q.lower() for q in self.memoria_corto_plazo]
        
        if is_repetition:
            self.estado_animo -= 2
            print(f"🧠 ¡Pregunta repetida detectada! Humor penalizado.")
        else:
            self.estado_animo += 0.5
        
        self.memoria_corto_plazo.append(pregunta_jugador)
        self.estado_animo = max(-5, min(5, self.estado_animo))
        print(f"🧠 Estado de ánimo actualizado: {self.estado_animo:.1f}")

        # --- PASO 2: LLAMADA AL VERIFICADOR (SECUENCIAL) ---
        prompt_verificador = PROMPT_VERIFICADOR_V1.format(
            nombre_personaje=nombre_secreto,
            pregunta_usuario=pregunta_jugador
        )
        verificacion_g4f = await self._llamar_a_g4f(prompt_verificador, timeout=20)
        print(f"🔍 Filtro de Verificación para '{pregunta_jugador}': g4f dice -> {verificacion_g4f}")

        if not verificacion_g4f:
            verificacion_g4f = "AMBIGUOUS" # Si el verificador falla, asumimos ambigüedad

        # --- PASO 3: LLAMADA AL ORÁCULO CON PERSONALIDAD (CON EL RESULTADO DEL PASO 2) ---
        if self.estado_animo <= -3: estado_animo_texto = "Muy Negativo"
        elif self.estado_animo < 0: estado_animo_texto = "Negativo"
        elif self.estado_animo >= 3: estado_animo_texto = "Muy Positivo"
        elif self.estado_animo > 0: estado_animo_texto = "Positivo"
        else: estado_animo_texto = "Neutral"

        prompt_maestro = PROMPT_MAESTRO_ORACULO_V11_2.format(
            estado_animo_texto=estado_animo_texto,
            texto_del_jugador=pregunta_jugador,
            is_repetition=is_repetition,
            fact_check_result=verificacion_g4f.upper()
        )

        raw_response = await self._llamar_a_g4f(prompt_maestro)
        if not raw_response:
            return {"respuesta": "Dato ausente.", "aclaracion": "Mi mente está... nublada.", "game_over": False}

        try:
            json_str = raw_response[raw_response.find('{'):raw_response.rfind('}')+1]
            respuesta_ia = json.loads(json_str)
            
            # Filtro anti-spoiler
            aclaracion = respuesta_ia.get("aclaracion", "")
            if nombre_secreto.lower() in aclaracion.lower():
                respuesta_ia["aclaracion"] = "Casi revelo un secreto cósmico. Debo ser más cuidadoso."
            
            return respuesta_ia

        except Exception as e:
            print(f"🚨 Error al procesar la respuesta final del Oráculo: {e}")
            return {"respuesta": "Dato ausente.", "aclaracion": "Una turbulencia cósmica ha afectado mi visión.", "game_over": False}
