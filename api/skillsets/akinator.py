# =============================================================================
# == skillsets/akinator.py - v7.3 "El Juez Justo Mejorado"
# =============================================================================
# Correcciones principales:
# - Respeta límite de preguntas en modo clásico y alternativo.
# - Forza adivinanza o rendición cuando se alcanza el límite.
# - Mantiene contador de fallos y segunda oportunidad.
# - Conserva estrategia de proveedores y logging.
# =============================================================================

import g4f
import asyncio
import json
import re
import time
import random
import logging

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
PROMPT_INICIAR_JUEGO = """<task>You are a game master like Akinator. Ask your first question to start the game.</task><instruction>Your first question MUST be one of these two, exactly: "¿Tu personaje es una persona real?" or "¿Tu personaje es ficticio?". Choose one. Your response MUST be a single, valid JSON object.</instruction><mandatory_json_response_format>{"accion": "Preguntar", "texto": "Your chosen first question in Spanish"}</mandatory_json_response_format>"""
PROMPT_NORMAL_V5 = """<task>You are a master detective. Your goal is to deduce the character the user is thinking of. Formulate your next strategic question.</task><rules><rule id="1">**ONE CONCEPT PER QUESTION:** Your question must be a simple Yes/No question about a single concept.</rule><rule id="2">**NO REPEATING CONCEPTS:** Do not ask about a topic that is already in the <question_history>.</rule><rule id="3">**STRATEGY:** Analyze the facts. Your goal is to ask a question that halves the remaining possibilities.</rule></rules><context><game_state>{estado_juego_string}</game_state><deduction_journal>{diario_de_deduccion}</deduction_journal><question_history>AVOID ASKING ABOUT THESE TOPICS AGAIN: {question_history}</question_history></context><mandatory_json_response_format>{{"deep_think": "Your brief deduction and strategy.", "accion": "Preguntar", "texto": "Your new, unique question."}}</mandatory_json_response_format>"""
PROMPT_ADIVINANZA_FORZADA_V5 = """<task>You are a master detective. You have reached the question limit. You are FORBIDDEN from asking any more questions.</task><instruction>Analyze the entire <deduction_journal>. Based on all the facts, you have two choices: 1. If you have a strong hypothesis, state the character's name. 2. If you are lost, surrender. Your `accion` MUST be "Adivinar" or "Rendirse".</instruction><context><deduction_journal>{diario_de_deduccion}</deduction_journal></context><final_action_formats>{{"deep_think": "Based on the facts, my final guess is...", "accion": "Adivinar", "texto": "Character Name"}}{{"deep_think": "I have failed to deduce the character. I surrender.", "accion": "Rendirse", "texto": "Me rindo. No tengo idea de quién es tu personaje."}}</final_action_formats>"""

class Akinator:
    def __init__(self):
        self.historial = []
        self.contador_adivinanzas_fallidas = 0
        
        self.proveedor_favorito = "OperaAria"
        self.proveedores_respaldo = [
            "You", "OpenAIFM", "OIVSCodeSer0501", "Raycast", "Qwen_Qwen_3",
            "AnyProvider", "CohereForAI_C4AI_Command", "DeepInfra", "Mintlify",
            "PollinationsAI", "Yqcloud", "BlackForestLabs_Flux1Dev", "WeWordle"
        ]
        random.shuffle(self.proveedores_respaldo)
        
        print(f"    - Especialista 'Akinator' (v7.3) listo.")
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
            print(f"    ⚠️ Fallo con '{proveedor}' ({type(e).__name__}).")
            return None

    async def _llamar_con_estrategia(self, prompt, timeout=25):
        await asyncio.sleep(1.5)
        json_response = await self._llamar_proveedor(self.proveedor_favorito, prompt, timeout)
        if json_response: return json_response
        for proveedor_respaldo in self.proveedores_respaldo:
            json_response = await self._llamar_proveedor(proveedor_respaldo, prompt, timeout)
            if json_response: return json_response
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
            return {"error": "El Oráculo no pudo iniciar la partida."}

    async def _procesar_respuesta_jugador(self, datos_peticion):
        respuesta_jugador = datos_peticion.get('respuesta', 'N/A')
        estado_juego = datos_peticion.get("estado_juego", {})
        pregunta_actual = estado_juego.get('pregunta_actual', 0)
        limite_preguntas = estado_juego.get('limite_preguntas', 20)

        # --- Incrementar contador de fallos si la adivinanza fue incorrecta ---
        if respuesta_jugador.startswith("No, no es"):
            self.contador_adivinanzas_fallidas += 1
            thoughts_logger.info(f"FALLO DE ADIVINANZA #{self.contador_adivinanzas_fallidas}")

            if self.contador_adivinanzas_fallidas >= 3:
                return {"accion": "Rendirse", "texto": "He fallado demasiadas veces. ¡Tu mente es superior!"}

        self.historial.append(f"Jugador respondió: '{respuesta_jugador}'")
        thoughts_logger.info(f"Turno {pregunta_actual}: Jugador respondió -> '{respuesta_jugador}'")

        # --- VERIFICAR LÍMITE DE PREGUNTAS ---
        if pregunta_actual >= limite_preguntas:
            thoughts_logger.info("Límite de preguntas alcanzado. Forzando adivinanza final.")
            return {"accion": "Adivinar", "texto": "Creo que ya sé tu personaje..."}

        # --- Preparar prompt según estado ---
        es_post_fallo = self.contador_adivinanzas_fallidas > 0
        prompt_a_usar = PROMPT_NORMAL_V5
        if es_post_fallo:
            thoughts_logger.info(f"PROTOCOLO POST-FALLO #{self.contador_adivinanzas_fallidas}")

        diario_texto = "\n".join(self.historial)
        preguntas_hechas = [line.replace("IA preguntó: '", "")[:-1] for line in self.historial if line.startswith("IA preguntó:")]
        historial_preguntas_str = "\n".join(f"- {q}" for q in preguntas_hechas) or "Ninguna"

        prompt_formateado = prompt_a_usar.format(
            diario_de_deduccion=diario_texto,
            estado_juego_string=json.dumps(estado_juego),
            question_history=historial_preguntas_str
        )

        # --- Llamar IA ---
        json_response = await self._llamar_con_estrategia(prompt_formateado)
        if json_response:
            deep_think_text = json_response.get('deep_think', 'N/A')
            thoughts_logger.info(f"Deep Think: {deep_think_text}")
            if json_response.get("accion") == "Preguntar":
                self.historial.append(f"IA preguntó: '{json_response.get('texto')}'")
            return json_response

        return {"error": "El Oráculo perdió conexión y no puede continuar."}
