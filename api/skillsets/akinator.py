# =============================================================================
# == skillsets/akinator.py - v7.2 "El Juez Justo"
# =============================================================================
# - LÓGICA DE CONTADOR DE FALLOS: Implementa un contador para permitir
#   exactamente dos "segundas oportunidades" antes de la derrota.
# - AUMENTO DE LÍMITE CONTROLADO: Añade preguntas extra en cada fallo,
#   pero solo dos veces.
# - DERROTA INEVITABLE: Al tercer fallo, la IA se rinde sin más intentos.
# - MANTIENE ESTRATEGIA v7.0: Sigue priorizando 'OperaAria' con respiro.
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

# --- PROMPTS DE IA (v5.1 - Sin cambios) ---
PROMPT_INICIAR_JUEGO = """<task>You are a game master like Akinator. Ask your first question to start the game.</task><instruction>Your first question MUST be one of these two, exactly: "¿Tu personaje es una persona real?" or "¿Tu personaje es ficticio?". Choose one. Your response MUST be a single, valid JSON object.</instruction><mandatory_json_response_format>{"accion": "Preguntar", "texto": "Your chosen first question in Spanish"}</mandatory_json_response_format>"""
PROMPT_NORMAL_V5 = """<task>You are a master detective. Your goal is to deduce the character the user is thinking of. Formulate your next strategic question.</task><rules><rule id="1">**ONE CONCEPT PER QUESTION:** Your question must be a simple Yes/No question about a single concept. Example: "Is your character a superhero?" is GOOD. "Is your character a superhero or a villain?" is BAD.</rule><rule id="2">**NO REPEATING CONCEPTS:** Do not ask about a topic that is already in the <question_history>.</rule><rule id="3">**STRATEGY:** Analyze the facts. Your goal is to ask a question that halves the remaining possibilities. If you detect a transmedia character (exists in movies, books, and games), your priority is to find the original source material.</rule></rules><context><game_state>{estado_juego_string}</game_state><deduction_journal>{diario_de_deduccion}</deduction_journal><question_history>AVOID ASKING ABOUT THESE TOPICS AGAIN: {question_history}</question_history></context><mandatory_json_response_format>{{"deep_think": "Your brief deduction and strategy.", "accion": "Preguntar", "texto": "Your new, unique question."}}</mandatory_json_response_format>"""
PROMPT_ADIVINANZA_FORZADA_V5 = """<task>You are a master detective. You have reached the question limit. You are FORBIDDEN from asking any more questions.</task><instruction>Analyze the entire <deduction_journal>. Based on all the facts, you have two choices: 1. If you have a strong hypothesis, state the character's name. 2. If you are lost, surrender. Your `accion` MUST be "Adivinar" or "Rendirse".</instruction><context><deduction_journal>{diario_de_deduccion}</deduction_journal></context><final_action_formats>{{"deep_think": "Based on the facts, my final guess is...", "accion": "Adivinar", "texto": "Character Name"}}{{"deep_think": "I have failed to deduce the character. I surrender.", "accion": "Rendirse", "texto": "Me rindo. No tengo idea de quién es tu personaje."}}</final_action_formats>"""

class Akinator:
    def __init__(self):
        self.historial = []
        self.contador_adivinanzas_fallidas = 0 # <-- ¡EL NUEVO CONTADOR!
        
        self.proveedor_favorito = "OperaAria"
        self.proveedores_respaldo = [
            "You", "OpenAIFM", "OIVSCodeSer0501", "Raycast", "Qwen_Qwen_3",
            "AnyProvider", "CohereForAI_C4AI_Command", "DeepInfra", "Mintlify",
            "PollinationsAI", "Yqcloud", "BlackForestLabs_Flux1Dev", "WeWordle"
        ]
        random.shuffle(self.proveedores_respaldo)
        
        print(f"    - Especialista 'Akinator' (v7.2 - El Juez Justo) listo.")
        print(f"      Estrategia: '{self.proveedor_favorito}' primero, con respiro de 1.5s.")
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
        await asyncio.sleep(1.5)
        print(f"    >> [Plan A] Intentando con el favorito '{self.proveedor_favorito}'...")
        json_response = await self._llamar_proveedor(self.proveedor_favorito, prompt, timeout)
        if json_response:
            return json_response

        print(f"    🚨 Fallo con el favorito. Activando Plan B...")
        for proveedor_respaldo in self.proveedores_respaldo:
            print(f"    >> [Plan B] Intentando con '{proveedor_respaldo}'...")
            json_response = await self._llamar_proveedor(proveedor_respaldo, prompt, timeout)
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
        self.contador_adivinanzas_fallidas = 0 # Reseteamos el contador
        
        json_response = await self._llamar_con_estrategia(PROMPT_INICIAR_JUEGO)
        
        if json_response and json_response.get("accion") == "Preguntar":
            pregunta = json_response.get('texto')
            self.historial.append(f"IA preguntó: '{pregunta}'")
            thoughts_logger.info(f"INICIO DE JUEGO. Pregunta 1: {pregunta}")
            return json_response
        else:
            return {"error": "El Oráculo no pudo iniciar la partida. Ningún proveedor está disponible."}

    async def _procesar_respuesta_jugador(self, datos_peticion):
        respuesta_jugador = datos_peticion.get('respuesta', 'N/A')
        estado_juego = datos_peticion.get("estado_juego", {})
        
        # --- LÓGICA DEL JUEZ JUSTO ---
        if respuesta_jugador.startswith("No, no es"):
            self.contador_adivinanzas_fallidas += 1
            print(f"    ⚖️ Juez: Fallo de adivinanza #{self.contador_adivinanzas_fallidas} detectado.")
            thoughts_logger.info(f"FALLO DE ADIVINANZA #{self.contador_adivinanzas_fallidas}. Jugador corrigió: '{respuesta_jugador}'")

            if self.contador_adivinanzas_fallidas >= 3:
                print("    ⚖️ Juez: Tercer fallo. La IA ha perdido. Forzando rendición.")
                thoughts_logger.info("TERCER FALLO. Derrota automática de la IA.")
                return {"accion": "Rendirse", "texto": "He fallado demasiadas veces. Me has vencido. ¡Tu mente es superior!"}
        
        self.historial.append(f"Jugador respondió: '{respuesta_jugador}'")
        thoughts_logger.info(f"Turno {estado_juego.get('pregunta_actual', '?')}: Jugador respondió -> '{respuesta_jugador}'")

        # --- LÓGICA DEL DIRECTOR ---
        es_turno_de_adivinar = estado_juego.get('pregunta_actual', 0) >= estado_juego.get('limite_preguntas', 20)
        es_post_fallo = self.contador_adivinanzas_fallidas > 0

        if es_turno_de_adivinar and not es_post_fallo:
            print("    ✋ Límite de preguntas alcanzado. Forzando adivinanza final.")
            thoughts_logger.info("LÍMITE ALCANZADO. Usando prompt de adivinanza forzada.")
            prompt_a_usar = PROMPT_ADIVINANZA_FORZADA_V5
        else:
            prompt_a_usar = PROMPT_NORMAL_V5
            if es_post_fallo:
                print(f"    🧠 Forzando pregunta de seguimiento después del fallo #{self.contador_adivinanzas_fallidas}.")
                thoughts_logger.info(f"PROTOCOLO POST-FALLO #{self.contador_adivinanzas_fallidas}: Forzando uso de PROMPT_NORMAL_V5.")

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
        else:
            return {"error": "El Oráculo ha perdido la conexión con todas las realidades conocidas. No se puede continuar."}
