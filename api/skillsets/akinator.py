# =============================================================================
# == skillsets/akinator.py - v7.5 "El Juez Inteligente"
# =============================================================================
# - Permite ADIVINANZA TEMPRANA si la IA cree saber la respuesta.
# - El límite de 20 preguntas BLOQUEA PREGUNTAS, no la inteligencia.
# - Las segundas oportunidades son reales, no decorativas.
# - Al tercer fallo: rendición automática (sin drama técnico).
# - Base v7.2 respetada. Flujo estabilizado para demo/video.
# =============================================================================

import g4f
import asyncio
import json
import re
import random
import logging

# --- LOGGING ---
thoughts_logger = logging.getLogger('AkinatorThoughts')
thoughts_logger.setLevel(logging.INFO)
thoughts_logger.propagate = False
if not thoughts_logger.handlers:
    handler = logging.FileHandler('akinator_thoughts.log', mode='a', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    thoughts_logger.addHandler(handler)

# --- PROMPTS ---
PROMPT_INICIAR_JUEGO = """
<task>You are a master game host.</task>
<instruction>
Choose EXACTLY one:
"¿Tu personaje es una persona real?"
OR
"¿Tu personaje es ficticio?"
Respond only as JSON.
</instruction>
<mandatory_json_response_format>
{"accion":"Preguntar","texto":"Pregunta"}
</mandatory_json_response_format>
"""

PROMPT_NORMAL = """
<task>You are Akinator.</task>
<instruction>
You may either:
- Ask ONE yes/no question
- OR make a GUESS if you feel confident
</instruction>

<rules>
- One concept per question
- Do not repeat previous questions
- If your confidence is high, GUESS
</rules>

<context>
<game_state>{estado_juego}</game_state>
<deduction_journal>{diario}</deduction_journal>
<question_history>{historial_preguntas}</question_history>
</context>

<mandatory_json_response_format>
{"deep_think":"Reason briefly","accion":"Preguntar|Adivinar","texto":"Question or Character"}
</mandatory_json_response_format>
"""

PROMPT_ADIVINANZA_FINAL = """
<task>You reached the question limit.</task>
<instruction>
You are NOT allowed to ask questions.
You MUST either:
- Guess the character
- OR surrender
</instruction>

<context>
<deduction_journal>{diario}</deduction_journal>
</context>

<final_action_formats>
{"accion":"Adivinar","texto":"Character Name"}
{"accion":"Rendirse","texto":"Me rindo. No logré deducirlo."}
</final_action_formats>
"""

# =============================================================================

class Akinator:

    def __init__(self):
        self.historial = []
        self.fallos = 0
        self.proveedor_favorito = "OperaAria"
        self.proveedores_respaldo = [
            "You", "AnyProvider", "Raycast", "Qwen_Qwen_3"
        ]
        random.shuffle(self.proveedores_respaldo)
        print("🧠 Akinator v7.5 listo.")
        thoughts_logger.info("=== NUEVA SESIÓN ===")

    # ---------- UTILS ----------

    def _extraer_json(self, texto):
        if not texto:
            return None
        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    async def _llamar(self, proveedor, prompt):
        try:
            resp = await g4f.ChatCompletion.create_async(
                model="gpt-4",
                provider=getattr(g4f.Provider, proveedor),
                messages=[{"role": "user", "content": prompt}],
                timeout=25
            )
            return self._extraer_json(resp)
        except Exception:
            return None

    async def _llamar_con_estrategia(self, prompt):
        await asyncio.sleep(1.2)
        resp = await self._llamar(self.proveedor_favorito, prompt)
        if resp:
            return resp
        for p in self.proveedores_respaldo:
            resp = await self._llamar(p, prompt)
            if resp:
                return resp
        return None

    # ---------- API ----------

    async def ejecutar(self, datos):
        accion = datos.get("accion")
        if accion == "iniciar_juego_clasico":
            return await self._iniciar()
        if accion == "procesar_respuesta_jugador":
            return await self._procesar(datos)
        return {"error": "Acción desconocida"}

    async def _iniciar(self):
        self.historial = []
        self.fallos = 0
        resp = await self._llamar_con_estrategia(PROMPT_INICIAR_JUEGO)
        if resp:
            self.historial.append(f"IA: {resp['texto']}")
            return resp
        return {"error": "No se pudo iniciar"}

    async def _procesar(self, datos):
        respuesta = datos.get("respuesta", "")
        estado = datos.get("estado_juego", {})
        pregunta_actual = estado.get("pregunta_actual", 0)
        limite = estado.get("limite_preguntas", 20)

        # ---- fallo ----
        if respuesta.startswith("No, no es"):
            self.fallos += 1
            thoughts_logger.info(f"FALLO #{self.fallos}")
            if self.fallos >= 3:
                return {"accion": "Rendirse", "texto": "He fallado demasiadas veces."}

        self.historial.append(f"Jugador: {respuesta}")

        diario = "\n".join(self.historial)
        preguntas = [h.replace("IA: ", "") for h in self.historial if h.startswith("IA:")]
        historial_preguntas = "\n".join(preguntas) or "Ninguna"

        # ---- decidir prompt ----
        if pregunta_actual >= limite:
            prompt = PROMPT_ADIVINANZA_FINAL.format(diario=diario)
        else:
            prompt = PROMPT_NORMAL.format(
                estado_juego=json.dumps(estado),
                diario=diario,
                historial_preguntas=historial_preguntas
            )

        resp = await self._llamar_con_estrategia(prompt)
        if not resp:
            return {"error": "El Oráculo no respondió"}

        if resp.get("accion") == "Preguntar":
            self.historial.append(f"IA: {resp['texto']}")

        return resp
