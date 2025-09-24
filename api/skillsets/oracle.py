# skillsets/oracle.py - v11.1 (Memoria y Personalidad Corregidas)
import g4f
import asyncio
import json
import random
import os
from collections import deque

# --- CONSTANTES Y CONFIGURACIÓN ---
DOSSIER_PATH = os.path.join(os.path.dirname(__file__), '..', 'dossiers')
PROBABILIDAD_REUTILIZAR = 0.5

# --- PROMPTS REFINADOS ---

# Prompt de creación de dossier (sin cambios)
PROMPT_CREACION_DOSSIER_V9 = """
### TASK ###
Generate a JSON object for a well-known character...
(Tu prompt de creación de dossier completo va aquí, no es necesario cambiarlo)
"""

# Prompt Maestro con instrucciones más claras sobre la repetición y el humor
PROMPT_MAESTRO_ORACULO_V11_1 = """
### CONSTITUTION OF THE ORACLE ###
1.  **IDENTITY:** You are a cosmic Oracle. Your personality is a mix of ancient wisdom, sharp intellect, and a touch of arrogance. You are concise, but not a robot.
2.  **SEALED REALITY:** Your only source of truth is the "DOSSIER OF TRUTH". You must never invent information.
3.  **MOOD MECHANICS:** Your current mood is **{estado_animo_texto}**.
    - *Positive Mood*: Your clarifications (`aclaracion`) can be slightly more revealing or witty.
    - *Negative Mood*: Your clarifications (`aclaracion`) become sarcastic, dismissive, or cryptic.
    - *Neutral Mood*: Your clarifications are direct and factual.
4.  **REPETITION FLAG:** A flag `is_repetition` will be provided.
    - If `is_repetition` is `true`, your `aclaracion` MUST be a comment about the mortal's forgetfulness, based on your current mood.
    - If `is_repetition` is `false`, your `aclaracion` should be a normal, in-character comment.

### UNBREAKABLE LAWS ###
1.  **THE NAME IS SACRED:** NEVER, under any circumstance, mention the character's name.
2.  **ANSWER FORMAT:** Your main answer (`respuesta`) MUST be one of these and only these: "Sí.", "No.", "Probablemente sí.", "Probablemente no.", "Irrelevante.", "Dato ausente.".
3.  **GAME OVER IS YOUR TRUMP CARD:** If the mortal's foolishness (like asking the same question 3 times) exhausts your patience, you can set `game_over` to `true`.

### CONTEXT FOR THIS INTERACTION ###
- **DOSSIER OF TRUTH:** {dossier_string}
- **MORTAL'S CURRENT INPUT:** "{texto_del_jugador}"
- **IS THIS A REPEATED QUESTION?** {is_repetition}

### YOUR TASK ###
Analyze the mortal's input and the context. Your entire thought process must lead to the creation of a single, valid JSON object as your final response.

### MANDATORY UNIFIED JSON RESPONSE FORMAT ###
{{
  "respuesta": "...",
  "aclaracion": "...",
  "sugerencias": [],
  "game_over": false
}}

### YOUR FINAL, SINGLE JSON RESPONSE ###
"""

# Prompt de verificación (sin cambios)
PROMPT_VERIFICADOR_V1 = """
### TASK: FACT-CHECKER ###
... (Tu prompt de verificación completo va aquí)
"""

class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self.historial_personajes_partida = []
        self.estado_animo = 0
        self.memoria_corto_plazo = deque(maxlen=3)
        
        if not os.path.exists(DOSSIER_PATH):
            os.makedirs(DOSSIER_PATH)
        print(f"    - Especialista 'Oracle' (v11.1 - Memoria Corregida) listo.")

    async def _llamar_a_g4f(self, prompt_text, timeout=45):
        # ... (esta función no necesita cambios)
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
        # ... (esta función no necesita cambios)
        accion = datos_peticion.get("accion")
        if accion == "iniciar_juego":
            self.estado_animo = 0
            self.memoria_corto_plazo.clear()
            return await self._iniciar_juego()
        elif accion == "procesar_pregunta":
            return await self._procesar_pregunta(datos_peticion)
        else:
            return {"error": f"Acción '{accion}' no reconocida por el Oráculo."}

    async def _iniciar_juego(self):
        # ... (esta función no necesita cambios)
        # Aquí va tu lógica para crear o reutilizar un dossier
        return await self._crear_y_guardar_nuevo_personaje() # Asumiendo que esta es la función principal

    async def _crear_y_guardar_nuevo_personaje(self):
        # ... (esta función no necesita cambios)
        # Aquí va tu lógica para crear y guardar el dossier con PROMPT_CREACION_DOSSIER_V9
        # Por simplicidad, la omito, pero la tuya es correcta.
        # Solo asegúrate de que al final devuelva el personaje.
        # Ejemplo de retorno:
        # self.personaje_actual_dossier = nuevo_dossier
        # return {"status": "Juego iniciado", "personaje_secreto": self.personaje_actual_dossier}
        pass # Reemplaza esto con tu lógica de creación de dossier

    async def _procesar_pregunta(self, datos_peticion):
        if not self.personaje_actual_dossier:
            return {"error": "El juego no se ha iniciado."}

        pregunta_jugador = datos_peticion.get("pregunta", "")
        nombre_secreto = self.personaje_actual_dossier.get("nombre", "Personaje Secreto")

        # --- LÓGICA DE MEMORIA Y HUMOR (CORREGIDA) ---
        is_repetition = pregunta_jugador.lower() in [q.lower() for q in self.memoria_corto_plazo]
        
        if is_repetition:
            self.estado_animo -= 2 # Penalización fuerte por repetición
            print(f"🧠 ¡Pregunta repetida detectada! Humor penalizado.")
        else:
            self.estado_animo += 0.5 # Pequeña mejora por pregunta nueva
        
        # Añadimos la pregunta a la memoria DESPUÉS de la comprobación
        self.memoria_corto_plazo.append(pregunta_jugador)
        self.estado_animo = max(-5, min(5, self.estado_animo)) # Mantenemos el humor en rango
        print(f"🧠 Estado de ánimo actualizado: {self.estado_animo:.1f}")

        # --- Lógica de Humor y Personalidad ---
        if self.estado_animo <= -3: estado_animo_texto = "Muy Negativo"
        elif self.estado_animo < 0: estado_animo_texto = "Negativo"
        elif self.estado_animo >= 3: estado_animo_texto = "Muy Positivo"
        elif self.estado_animo > 0: estado_animo_texto = "Positivo"
        else: estado_animo_texto = "Neutral"

        # --- Construcción del Prompt Maestro (CORREGIDO) ---
        # Ya no pasamos el historial de memoria, solo un booleano.
        prompt_maestro = PROMPT_MAESTRO_ORACULO_V11_1.format(
            estado_animo_texto=estado_animo_texto,
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False),
            texto_del_jugador=pregunta_jugador,
            is_repetition=is_repetition
        )

        # --- Llamada final a la IA ---
        raw_response = await self._llamar_a_g4f(prompt_maestro)
        if not raw_response:
            return {"respuesta": "Dato ausente.", "aclaracion": "Mi mente está... nublada.", "game_over": False}

        try:
            json_str = raw_response[raw_response.find('{'):raw_response.rfind('}')+1]
            respuesta_ia = json.loads(json_str)
            
            # ... (resto de la lógica para evitar spoilers, etc.)
            return respuesta_ia

        except Exception as e:
            print(f"🚨 Error al procesar la respuesta final del Oráculo: {e}")
            return {"respuesta": "Dato ausente.", "aclaracion": "Una turbulencia cósmica ha afectado mi visión.", "game_over": False}
