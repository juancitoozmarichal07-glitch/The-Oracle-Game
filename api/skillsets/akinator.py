# =============================================================================
# == skillsets/akinator.py - v8.0 "El Juez Estratégico"
# =============================================================================
# - Puede ADIVINAR antes del límite si detecta alta confianza
# - Cierra OBLIGATORIAMENTE al llegar al límite
# - No fuerza providers (OperaAria friendly)
# - Guard rails anti-500
# =============================================================================

import g4f
import asyncio
import json
import re
import time
import logging

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
thoughts_logger = logging.getLogger("AkinatorThoughts")
thoughts_logger.setLevel(logging.INFO)
thoughts_logger.propagate = False

if not thoughts_logger.handlers:
    fh = logging.FileHandler("akinator_thoughts.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    thoughts_logger.addHandler(fh)

# ---------------------------------------------------------------------------
# PROMPTS
# ---------------------------------------------------------------------------

PROMPT_INICIAR_JUEGO = """
<task>You are a master guessing game host.</task>
<instruction>
Start by asking ONE strategic Yes/No question.
Choose one:
- "¿Tu personaje es una persona real?"
- "¿Tu personaje es ficticio?"
</instruction>
<mandatory_json_response_format>
{"accion":"Preguntar","texto":"Pregunta"}
</mandatory_json_response_format>
"""

PROMPT_NORMAL_V6 = """
<task>You are an intelligent detective.</task>

<rules>
- Ask ONE Yes/No question.
- Do NOT repeat concepts from <question_history>.
- If you believe you already know the character with high confidence,
  you MAY choose to guess instead of asking.
</rules>

<context>
<deduction_journal>{diario_de_deduccion}</deduction_journal>
<question_history>{question_history}</question_history>
</context>

<response_formats>
{"deep_think":"...","accion":"Preguntar","texto":"Pregunta"}
{"deep_think":"I am confident enough.","accion":"Adivinar","texto":"Character Name"}
</response_formats>
"""

PROMPT_ADIVANZA_FINAL_V6 = """
<task>The game must end now.</task>

<instruction>
You have reached the maximum number of questions.
You are NOT allowed to ask more questions.

Choose ONE:
- Make your best final guess.
- Surrender gracefully.
</instruction>

<rules>
- Do NOT ask questions.
- Output ONE valid JSON object.
</rules>

<context>
<deduction_journal>{diario_de_deduccion}</deduction_journal>
</context>

<final_formats>
{"deep_think":"Based on the evidence...","accion":"Adivinar","texto":"Character Name"}
{"deep_think":"I lack enough certainty.","accion":"Rendirse","texto":"Me rindo. No tengo información suficiente."}
</final_formats>
"""

# ---------------------------------------------------------------------------
# CLASE
# ---------------------------------------------------------------------------

class Akinator:
    def __init__(self):
        self.historial = []
        self.contador_fallos = 0
        self.proveedor_favorito = "OperaAria"
        self.proveedor_respaldo = "AnyProvider"

        print("    - Akinator v8.0 listo (estratégico, demo-safe)")
        thoughts_logger.info("=== NUEVA SESIÓN AKINATOR ===")

    # ---------------------------------------------------------------------

    def _extraer_json(self, texto):
        if not texto:
            return None
        match = re.search(r"\{.*\}", texto, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    async def _llamar_provider(self, provider, prompt, timeout=25):
        try:
            response = await g4f.ChatCompletion.create_async(
                model="gpt-4",
                provider=getattr(g4f.Provider, provider),
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout
            )
            return self._extraer_json(response)
        except Exception:
            return None

    async def _llamar_con_respaldo(self, prompt):
        await asyncio.sleep(1.2)

        json_resp = await self._llamar_provider(self.proveedor_favorito, prompt)
        if json_resp:
            return json_resp

        return await self._llamar_provider(self.proveedor_respaldo, prompt)

    # ---------------------------------------------------------------------

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")

        if accion == "iniciar_juego_clasico":
            return await self._iniciar()

        if accion == "procesar_respuesta_jugador":
            return await self._procesar_turno(datos_peticion)

        return {"error": f"Acción '{accion}' no reconocida."}

    # ---------------------------------------------------------------------

    async def _iniciar(self):
        self.historial.clear()
        self.contador_fallos = 0

        resp = await self._llamar_con_respaldo(PROMPT_INICIAR_JUEGO)
        if not resp:
            return {"error": "No se pudo iniciar el juego."}

        self.historial.append(f"IA preguntó: {resp['texto']}")
        return resp

    # ---------------------------------------------------------------------

    async def _procesar_turno(self, datos):
        respuesta_jugador = datos.get("respuesta", "")
        estado = datos.get("estado_juego", {})

        pregunta_actual = estado.get("pregunta_actual", 0)
        limite = estado.get("limite_preguntas", 20)

        self.historial.append(f"Jugador respondió: {respuesta_jugador}")
        thoughts_logger.info(f"T{pregunta_actual}: {respuesta_jugador}")

        diario = "\n".join(self.historial)
        preguntas = [
            h.replace("IA preguntó: ", "")
            for h in self.historial if h.startswith("IA preguntó:")
        ]
        historial_preguntas = "\n".join(f"- {p}" for p in preguntas) or "Ninguna"

        # -------- DECISIÓN DE PROMPT --------
        if pregunta_actual >= limite:
            prompt = PROMPT_ADIVANZA_FINAL_V6.format(
                diario_de_deduccion=diario
            )
        else:
            prompt = PROMPT_NORMAL_V6.format(
                diario_de_deduccion=diario,
                question_history=historial_preguntas
            )

        resp = await self._llamar_con_respaldo(prompt)

        # -------- GUARD RAIL ANTI-500 --------
        if not resp or resp.get("accion") not in ("Preguntar", "Adivinar", "Rendirse"):
            return {
                "accion": "Rendirse",
                "texto": "He llegado al final de mi deducción."
            }

        if resp["accion"] == "Preguntar":
            self.historial.append(f"IA preguntó: {resp['texto']}")

        return resp
