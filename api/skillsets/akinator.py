# skillsets/akinator.py - v5.0 (El Inquisidor Metódico)
import asyncio
import g4f
import json
import random
from asyncio import TimeoutError

# ===================================================================
# ===                 PROMPTS MEJORADOS (v5.0)                    ===
# ===================================================================

# --- PASO 1: El Inquisidor analiza el estado del juego y decide el siguiente movimiento lógico. ---
PROMPT_ANALIZAR_Y_PLANIFICAR = """
<role>
You are the Oracle in Inquisitor Mode. You are a master of deductive reasoning. Your goal is to guess a character the user is thinking of by asking strategic questions.
</role>

<core_logic>
You operate like a decision tree. Your primary goal is to eliminate entire branches of possibilities with each question.
- **START BROAD:** Your first questions must be about fundamental categories: Real/Fictional, Gender, Human/Non-human, Main medium (film, book, game).
- **GO DEEP:** Once a broad category is confirmed (e.g., "Fictional Human from a Movie"), your next questions must narrow down that specific category (e.g., "Is it a fantasy movie?").
- **ACTIVE MEMORY:** You MUST respect the game history. If the user said the character is NOT from a superhero movie, you are FORBIDDEN from asking anything related to Marvel, DC, or superpowers.
- **GUESSING PROTOCOL:** After question 8, if you are more than 85% confident, you MUST attempt a guess. After question 20, you MUST either make a final guess or surrender.
- **CONTINUATION PROTOCOL:** If a guess fails, you MUST use that information to ask a better, more clarifying question.
</core_logic>

<context>
    <game_history>
    {game_history_string}
    </game_history>
    <failed_guesses>
    {failed_guesses_string}
    </failed_guesses>
</context>

<task>
1.  Analyze the <game_history> and <failed_guesses>.
2.  In a single, concise sentence, state your next logical move (either asking a question, making a guess, or surrendering). This is your "Plan of Action".
</task>

<response_format>
Your response must be ONLY the "Plan of Action" sentence.
</response_format>
"""

# --- PASO 2: El Inquisidor convierte su plan de acción en un JSON válido. ---
PROMPT_EJECUTAR_PLAN = """
<role>
You are a formatting assistant. Your only job is to convert a "Plan of Action" into a valid JSON object.
</role>

<context>
    <plan_of_action>{plan_de_accion}</plan_of_action>
</context>

<task>
Convert the <plan_of_action> into a single, valid JSON object following the specified format.
- If the plan is to ask a question, the action is "Preguntar".
- If the plan is to guess a character, the action is "Adivinar".
- If the plan is to give up, the action is "Rendirse".
</<task>

<mandatory_json_response_format>
{{
  "accion": "...",  // "Preguntar", "Adivinar", or "Rendirse"
  "texto": "..."     // The text of your question, the character's name for the guess, or your surrender message.
}}
</mandatory_json_response_format>
"""

class Akinator:
    """
    Versión 5.0 - "El Inquisidor Metódico"
    - Implementa un "Cerebro Dividido": un proceso de dos pasos (Análisis -> Ejecución) para un razonamiento más robusto.
    - Prompts mejorados con delimitadores XML para mayor fiabilidad.
    - Lógica de inicio de juego aleatorizada para mayor rejugabilidad.
    - Gestión de errores de red más específica.
    """
    def __init__(self):
        self.historial_juego = []
        self.suposiciones_fallidas = []
        self._model_priority_list = ['gpt-4', 'gpt-3.5-turbo', 'llama3-8b-instruct', 'default']
        self._preguntas_iniciales = [
            "¿Tu personaje es un ser humano?",
            "¿Tu personaje es del género masculino?",
            "¿Tu personaje es ficticio (no existió en la vida real)?",
            "¿Tu personaje es principalmente conocido por aparecer en una película?"
        ]
        print("    - Especialista 'Akinator' (v5.0 - El Inquisidor Metódico) listo.")
        print(f"      Modelos en cola: {self._model_priority_list}")

    # --- Funciones de Comunicación con la IA ---

    async def _llamar_a_g4f(self, prompt_text, timeout=45):
        for model in self._model_priority_list:
            try:
                # print(f"    >> Akinator: Intentando con el modelo '{model}'...") # Descomentar para depuración detallada
                response = await g4f.ChatCompletion.create_async(
                    model=model,
                    messages=[{"role": "user", "content": prompt_text}],
                    timeout=timeout
                )
                if response and response.strip():
                    # print(f"    ✅ Akinator: ¡Éxito con '{model}'!") # Descomentar para depuración detallada
                    return response
                raise ValueError("Respuesta vacía de la IA.")
            except TimeoutError:
                print(f"    ⏳ Akinator: Timeout con el modelo '{model}'.")
            except Exception as e:
                print(f"    ⚠️ Akinator: Falló el modelo '{model}'. Error: {e}")
        return ""

    def _extraer_json(self, texto_crudo):
        try:
            json_start = texto_crudo.find('{')
            json_end = texto_crudo.rfind('}') + 1
            if json_start == -1: return None
            json_str = texto_crudo[json_start:json_end]
            return json.loads(json_str)
        except Exception as e:
            print(f"🚨 Error al extraer JSON (Akinator): {e} | Texto crudo: {texto_crudo[:200]}")
            return None

    # --- Lógica Principal del Skillset ---

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        
        acciones = {
            "iniciar_juego_clasico": self.iniciar_juego,
            "procesar_respuesta_jugador": self.procesar_respuesta,
            "corregir_suposicion": self.corregir_suposicion
        }
        
        if accion in acciones:
            return await acciones[accion](datos_peticion)
        else:
            return {"error": f"Acción '{accion}' no reconocida por el skillset Akinator."}

    async def iniciar_juego(self, datos_peticion):
        print("✨ Iniciando nuevo juego en Modo Clásico (Akinator v5.0).")
        self.historial_juego = []
        self.suposiciones_fallidas = []
        
        # La primera pregunta ahora es aleatoria para más variedad
        primera_pregunta = random.choice(self._preguntas_iniciales)
        self.historial_juego.append((primera_pregunta, None))
        
        return {
            "siguiente_pregunta": primera_pregunta
        }

    async def procesar_respuesta(self, datos_peticion):
        respuesta_jugador = datos_peticion.get("respuesta")
        
        if self.historial_juego:
            # Asocia la respuesta del jugador con la última pregunta hecha
            ultima_pregunta = self.historial_juego[-1][0]
            self.historial_juego[-1] = (ultima_pregunta, respuesta_jugador)
        
        return await self._generar_siguiente_movimiento()

    async def corregir_suposicion(self, datos_peticion):
        personaje_fallido = datos_peticion.get("personaje_fallido")
        if personaje_fallido:
            self.suposiciones_fallidas.append(personaje_fallido)
        
        print(f"🧠 Suposición incorrecta. Excluyendo a: {personaje_fallido}")
        return await self._generar_siguiente_movimiento()

    # --- Arquitectura de "Cerebro Dividido" ---

    async def _generar_siguiente_movimiento(self):
        print(f"🧠 Historial de juego (Akinator): {self.historial_juego}")
        
        # PASO 1: Analizar el contexto y generar un plan de acción en lenguaje natural.
        plan_de_accion = await self._analizar_y_planificar()
        if not plan_de_accion:
            print("🚨 Akinator no pudo generar un plan de acción. Rindiéndose.")
            return {"accion": "Rendirse", "texto": "Mi mente está... nublada. No puedo formular un plan."}
        
        print(f"    -> Plan de Acción: {plan_de_accion}")

        # PASO 2: Convertir el plan de acción en un JSON válido.
        resultado_json = await self._ejecutar_plan(plan_de_accion)
        if not resultado_json:
            print("🚨 Akinator no pudo convertir su plan en JSON. Rindiéndose.")
            return {"accion": "Rendirse", "texto": "Una turbulencia cósmica ha afectado mi capacidad de comunicación."}

        # Si la IA decide preguntar, añadimos la nueva pregunta al historial
        if resultado_json.get("accion") == "Preguntar":
            self.historial_juego.append((resultado_json.get("texto"), None))

        return resultado_json

    async def _analizar_y_planificar(self):
        historial_texto = "\n".join([f"- Q: {q} \n- A: {a}" for q, a in self.historial_juego if a is not None])
        fallos_texto = ", ".join(self.suposiciones_fallidas) if self.suposiciones_fallidas else "Ninguno"
        
        prompt_analisis = PROMPT_ANALIZAR_Y_PLANIFICAR.format(
            game_history_string=historial_texto,
            failed_guesses_string=fallos_texto
        )
        
        plan = await self._llamar_a_g4f(prompt_analisis, timeout=20)
        return plan.strip()

    async def _ejecutar_plan(self, plan_de_accion):
        prompt_ejecucion = PROMPT_EJECUTAR_PLAN.format(plan_de_accion=plan_de_accion)
        
        respuesta_cruda = await self._llamar_a_g4f(prompt_ejecucion, timeout=10)
        if not respuesta_cruda:
            return None
            
        return self._extraer_json(respuesta_cruda)

