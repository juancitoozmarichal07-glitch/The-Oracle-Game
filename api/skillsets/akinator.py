# =============================================================================
# == skillsets/akinator.py - v7.3 "El Juez Dramático"
# =============================================================================
# - Mantiene la lógica de contador de fallos: máximo 2 segundas oportunidades.
# - Mensajes y reacciones más humanas, con suspenso y dramatismo.
# - Logs más descriptivos sobre deducción y estrategia.
# - Mantiene estrategia con 'OperaAria' y respaldo, pero con narrativa.
# =============================================================================

import g4f
import asyncio
import json
import re
import time
import random
import logging
from collections import deque

# --- CONFIGURACIÓN DEL LOGGING ---
thoughts_logger = logging.getLogger('AkinatorThoughts')
thoughts_logger.setLevel(logging.INFO)
thoughts_logger.propagate = False
if not thoughts_logger.handlers:
    file_handler = logging.FileHandler('akinator_thoughts.log', mode='a', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    thoughts_logger.addHandler(file_handler)

# --- PROMPTS DE IA ---
# (Sin cambios funcionales, pero se pueden añadir toques dramáticos en texto)
PROMPT_INICIAR_JUEGO = """<task>You are a master game host. Start the game with suspense and flair.</task> 
<instruction>Choose first question exactly: "¿Tu personaje es una persona real?" or "¿Tu personaje es ficticio?". Respond as JSON.</instruction>
<mandatory_json_response_format>{"accion": "Preguntar", "texto": "Your chosen first question in Spanish"}</mandatory_json_response_format>
"""

PROMPT_NORMAL_V5 = """<task>You are a detective with intuition. Formulate your next strategic Yes/No question.</task>
<rules>
<rule id="1">Ask one concept per question.</rule>
<rule id="2">Avoid repeating concepts in <question_history>.</rule>
<rule id="3">Prioritize halving possibilities; detect transmedia origin.</rule>
</rules>
<context>
<game_state>{estado_juego_string}</game_state>
<deduction_journal>{diario_de_deduccion}</deduction_journal>
<question_history>{question_history}</question_history>
</context>
<mandatory_json_response_format>
{{"deep_think": "Your reasoning and suspenseful commentary.", "accion": "Preguntar", "texto": "Your new, unique question."}}
</mandatory_json_response_format>
"""

PROMPT_ADIVINANZA_FORZADA_V5 = """<task>You must conclude. Forbidden to ask more questions.</task>
<instruction>Analyze <deduction_journal>. Either make a confident guess or surrender gracefully.</instruction>
<context><deduction_journal>{diario_de_deduccion}</deduction_journal></context>
<final_action_formats>
{{"deep_think": "Based on facts, my final guess is...", "accion": "Adivinar", "texto": "Character Name"}}
{{"deep_think": "I have failed. Surrendering with dignity.", "accion": "Rendirse", "texto": "Me rindo. No sé quién es tu personaje."}}
</final_action_formats>
"""

class Akinator:
    def __init__(self):
        self.historial = []
        self.contador_adivinanzas_fallidas = 0
        self.proveedor_favorito = "OperaAria"
        self.proveedor_respaldo = "AnyProvider"

        print(f"    - Especialista 'Akinator' (v7.4 - El Juez Dramático) listo.")
        print(f"      Estrategia inicial: '{self.proveedor_favorito}' con respiro de 1.5s.")
        thoughts_logger.info("================= NUEVA SESIÓN DE AKINATOR INICIADA =================")

    def _extraer_json(self, texto_crudo):
        if not texto_crudo: return None
        texto_limpio = texto_crudo.strip()
        match = re.search(r'\{.*\}', texto_limpio, re.DOTALL)
        if match:
            try: return json.loads(match.group(0))
            except json.JSONDecodeError: return None
        return None

    async def _llamar_proveedor(self, proveedor, prompt, timeout):
        try:
            response = await g4f.ChatCompletion.create_async(
                model="gpt-4",
                provider=getattr(g4f.Provider, proveedor),
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout
            )
            json_response = self._extraer_json(response)
            if json_response:
                print(f"    ✅ Éxito con '{proveedor}'.")
                return json_response
            else:
                print(f"    ⚠️ Fallo de formato con '{proveedor}'.")
                return None
        except Exception as e:
            print(f"    ⚠️ Fallo de conexión/otro con '{proveedor}' ({type(e).__name__}).")
            return None

    async def _llamar_con_estrategia(self, prompt, timeout=25):
        await asyncio.sleep(1.5)  # Pequeña pausa de realismo
        print(f"    >> Intentando con favorito '{self.proveedor_favorito}'...")
        json_response = await self._llamar_proveedor(self.proveedor_favorito, prompt, timeout)
        if json_response:
            return json_response

        print(f"    🚨 Fallo favorito. Activando proveedor de respaldo '{self.proveedor_respaldo}'...")
        json_response = await self._llamar_proveedor(self.proveedor_respaldo, prompt, timeout)
        if json_response:
            return json_response

        return None

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        if accion == "iniciar_juego_clasico":
            return await self._iniciar_juego_clasico()
        elif accion == "procesar_respuesta_jugador":
            return await self._procesar_respuesta_jugador(datos_peticion)
        return {"error": f"Acción '{accion}' no reconocida."}

    async def _iniciar_juego_clasico(self):
        self.historial = []
        self.contador_adivinanzas_fallidas = 0
        json_response = await self._llamar_con_estrategia(PROMPT_INICIAR_JUEGO)
        if json_response and json_response.get("accion") == "Preguntar":
            pregunta = json_response.get('texto')
            self.historial.append(f"IA preguntó: '{pregunta}'")
            thoughts_logger.info(f"INICIO DE JUEGO. Pregunta 1: {pregunta}")
            return json_response
        else:
            return {"error": "El Oráculo no pudo iniciar la partida. Ningún proveedor disponible."}

    async def _procesar_respuesta_jugador(self, datos_peticion):
        respuesta_jugador = datos_peticion.get('respuesta', 'N/A')
        estado_juego = datos_peticion.get("estado_juego", {})

        # --- Contador de fallos ---
        if respuesta_jugador.startswith("No, no es"):
            self.contador_adivinanzas_fallidas += 1
            print(f"    ⚖️ Juez: Fallo #{self.contador_adivinanzas_fallidas} detectado.")
            thoughts_logger.info(f"FALLO DE ADIVINANZA #{self.contador_adivinanzas_fallidas}. Jugador corrigió: '{respuesta_jugador}'")
            if self.contador_adivinanzas_fallidas >= 3:
                print("    ⚖️ Juez: Tercer fallo. La IA se rinde.")
                thoughts_logger.info("TERCER FALLO. Derrota automática de la IA.")
                return {"accion": "Rendirse", "texto": "He fallado demasiadas veces. Me has vencido."}

        self.historial.append(f"Jugador respondió: '{respuesta_jugador}'")
        thoughts_logger.info(f"Turno {estado_juego.get('pregunta_actual', '?')}: Jugador respondió -> '{respuesta_jugador}'")

        # --- Determinar prompt ---
        es_turno_de_adivinar = estado_juego.get('pregunta_actual', 0) >= estado_juego.get('limite_preguntas', 20)
        es_post_fallo = self.contador_adivinanzas_fallidas > 0

        if es_turno_de_adivinar and not es_post_fallo:
            prompt_a_usar = PROMPT_ADIVANZA_FORZADA_V5
        else:
            prompt_a_usar = PROMPT_NORMAL_V5

        if es_post_fallo:
            thoughts_logger.info(f"PROTOCOLO POST-FALLO #{self.contador_adivinanzas_fallidas}: Usando PROMPT_NORMAL_V5.")

        diario_texto = "\n".join(self.historial)
        preguntas_hechas = [line.replace("IA preguntó: '", "")[:-1] for line in self.historial if line.startswith("IA preguntó:")]
        historial_preguntas_str = "\n".join(f"- {q}" for q in preguntas_hechas) or "Ninguna"

        prompt_formateado = prompt_a_usar.format(
            diario_de_deduccion=diario_texto,
            estado_juego_string=json.dumps(estado_juego),
            question_history=historial_preguntas_str
        )

        json_response = await self._llamar_con_estrategia(prompt_formateado)
        if json_response:
            deep_think_text = json_response.get('deep_think', 'N/A')
            thoughts_logger.info(f"Deep Think: {deep_think_text}")
            titular = (deep_think_text[:75] + '...') if len(deep_think_text) > 75 else deep_think_text
            print(f"    🧠 Deep Think: {titular}")

            if json_response.get("accion") == "Preguntar":
                self.historial.append(f"IA preguntó: '{json_response.get('texto')}'")
            return json_response

        return {"error": "El Oráculo no puede continuar."}
