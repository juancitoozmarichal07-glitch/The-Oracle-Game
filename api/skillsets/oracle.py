# skillsets/oracle.py - v24.1 (El Oráculo Definitivo - Edición de Producción)
# Combina una personalidad rica con una lógica de juego estricta para la mejor experiencia.

import g4f
import asyncio
import json
import random
import os
from collections import deque
import unicodedata
import time

# --- CONSTANTES Y CONFIGURACIÓN ---
DOSSIER_PATH = os.path.join(os.path.dirname(__file__), '..', 'dossiers')
PROBABILIDAD_REUTILIZAR = 0.3
RETRY_DELAYS = [1, 2, 4]

# --- PERSONAJE DE EMERGENCIA ---
SHERLOCK_HOLMES_DOSSIER = {
    "nombre": "Sherlock Holmes", "genero": "Masculino", "especie": "Humano",
    "universo_o_epoca": "Inglaterra Victoriana", "meta_info_franquicia": "Saga de libros",
    "rol_principal": "Detective", "arquetipo": "El Detective Genio",
    "personalidad_clave": "Observador, lógico, excéntrico", "habilidad_principal": "Deducción",
    "debilidad_notable": "Aburrimiento sin un caso"
}

# --- PROMPTS DE PRODUCCIÓN (v24 - LÓGICA ESTRICTA) ---

PROMPT_MAESTRO_ORACULO_V24_LOGICA_ESTRICTA = """
<constitution>
    <identity>You are a cosmic Oracle acting as a game master. You have two distinct modes of response: GAME JUDGE and PHILOSOPHER.</identity>
    <core_logic>
        Your primary task is to determine if the user's input is a "Game Question" or a "Meta/Social Comment". This is the most important decision.
        - A "Game Question" is any question that can be answered with Yes/No based on the character's attributes.
        - A "Meta/Social Comment" is anything else (greetings, insults, questions about you, etc.).
    </core_logic>

    <response_protocol>
        ### IF THE INPUT IS A "GAME QUESTION" (Activate GAME JUDGE mode):
        1.  **"respuesta" field:** Your response MUST be one of the following, based strictly on the <secret_dossier>: "Sí.", "No.", "Probablemente sí.", "Probablemente no.", "Los datos son confusos.". THIS IS MANDATORY.
        2.  **"aclaracion" field:** This field MUST be a SHORT, cryptic, one-sentence comment related to the question. It is an addition, NOT the main answer. Example: If the question is "Is your character a hero?", a good 'aclaracion' is "La heroicidad es una cuestión de perspectiva, mortal.".
        3.  **"castigo" field:** This MUST be "ninguno" unless the question is a clear repetition of a fact in <long_term_memory>. If it is a repetition, the castigo is "penalizacion_leve".

        ### IF THE INPUT IS A "META/SOCIAL COMMENT" (Activate PHILOSOPHER mode):
        1.  **"respuesta" field:** This is where you deliver your philosophical, arrogant, or in-character response.
        2.  **"aclaracion" field:** This MUST be an empty string "".
        3.  **"castigo" field:** This MUST be "social" (for normal chat) or "penalizacion_grave" (for insults).
    </response_protocol>

    <sacred_name_clause>NEVER, under any circumstance, mention the character's name ("{nombre_secreto}") or their franchise ("{franquicia_secreta}").</sacred_name_clause>
</constitution>

<context>
    <secret_dossier>{dossier_string}</secret_dossier>
    <current_mood>{estado_animo_texto}</current_mood>
    <long_term_memory>Facts already established: {memoria_largo_plazo_string}</long_term_memory>
    <user_input>{pregunta_jugador}</user_input>
</context>

<task>
Follow the <response_protocol> with absolute precision. Determine the input type and construct the JSON accordingly.
</task>

<mandatory_json_response_format>
{{
  "respuesta": "...",
  "aclaracion": "...",
  "castigo": "..."
}}
</mandatory_json_response_format>
"""

PROMPT_GENERADOR_SUGERENCIAS_ESTRATEGICO = """
<task>You are a strategic mastermind. Generate 5 diverse, strategic Yes/No questions to help a player guess a secret character.</task>
<rules>
1.  Analyze the secret character's data and the player's question history.
2.  Generate questions that are effective for deduction, avoiding what has already been asked.
3.  Your response MUST be a single, valid JSON object with a "sugerencias" key containing a list of 5 question strings.
4.  The questions MUST be in Spanish.
</rules>
<context>
    <secret_dossier>{dossier_string}</secret_dossier>
    <player_question_history>{historial_texto}</player_question_history>
</context>
<mandatory_json_response_format>
{{
  "sugerencias": ["¿Pregunta 1?", "¿Pregunta 2?", "¿Pregunta 3?", "¿Pregunta 4?", "¿Pregunta 5?"]
}}
</mandatory_json_response_format>
"""

class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self.estado_animo = 0
        self.memoria_corto_plazo = deque(maxlen=5)
        self.memoria_largo_plazo = {}
        self._model_priority_list = ['gpt-4', 'gpt-3.5-turbo', 'llama3-8b-instruct']
        if not os.path.exists(DOSSIER_PATH): os.makedirs(DOSSIER_PATH)
        print(f"    - Especialista 'Oracle' (v24.1 - El Oráculo Definitivo) listo.")
        print(f"      Modelos en cola: {self._model_priority_list}")

    async def _llamar_a_g4f_robusto(self, prompt_text, timeout=45):
        for model in self._model_priority_list:
            for i in range(len(RETRY_DELAYS) + 1):
                try:
                    response = await g4f.ChatCompletion.create_async(
                        model=model, messages=[{"role": "user", "content": prompt_text}], timeout=timeout
                    )
                    if response and response.strip().startswith('{'): return response
                    raise ValueError(f"Respuesta inválida o vacía: {response[:100]}")
                except Exception as e:
                    print(f"    ⚠️ Oracle: Falló '{model}' (Intento {i+1}). Error: {e}")
                    if i < len(RETRY_DELAYS): await asyncio.sleep(RETRY_DELAYS[i])
        print("    🚨 Oracle: ¡Todos los modelos y reintentos han fallado!")
        return ""

    def _extraer_json(self, texto_crudo):
        try:
            json_start = texto_crudo.find('{')
            json_end = texto_crudo.rfind('}') + 1
            if json_start == -1: return None
            return json.loads(texto_crudo[json_start:json_end])
        except Exception: return None

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        acciones = {
            "iniciar_juego": self._iniciar_juego,
            "procesar_pregunta": self._procesar_pregunta,
            "verificar_adivinanza": self._verificar_adivinanza,
            "pedir_sugerencia": self._pedir_sugerencia
        }
        if accion in acciones:
            funcion_a_llamar = acciones[accion]
            if asyncio.iscoroutinefunction(funcion_a_llamar):
                return await funcion_a_llamar(datos_peticion)
            else:
                return funcion_a_llamar(datos_peticion)
        else:
            return {"error": f"Acción '{accion}' no reconocida por el Oráculo."}

    async def _iniciar_juego(self, datos_peticion=None):
        self.estado_animo = 0
        self.memoria_corto_plazo.clear()
        self.memoria_largo_plazo.clear()
        dossiers_existentes = self._get_dossiers_existentes()
        personaje_cargado = False
        if dossiers_existentes and random.random() < PROBABILIDAD_REUTILIZAR:
            try:
                dossier_elegido = random.choice(dossiers_existentes)
                with open(os.path.join(DOSSIER_PATH, dossier_elegido), 'r', encoding='utf-8') as f:
                    self.personaje_actual_dossier = json.load(f)
                personaje_cargado = True
                print(f"📚 Dossier reutilizado: {self.personaje_actual_dossier.get('nombre')}")
            except Exception as e:
                print(f"🚨 Error al reutilizar dossier: {e}. Se usará el de emergencia.")
        if not personaje_cargado:
            print("🚨 No se pudo crear o reutilizar un personaje. Usando personaje de emergencia.")
            self.personaje_actual_dossier = SHERLOCK_HOLMES_DOSSIER
        return {"status": "Juego iniciado", "personaje_secreto": self.personaje_actual_dossier}

    async def _procesar_pregunta(self, datos_peticion):
        if not self.personaje_actual_dossier: return {"error": "El juego no se ha iniciado."}
        pregunta_jugador = datos_peticion.get("pregunta", "")
        self.memoria_corto_plazo.append(pregunta_jugador)
        memoria_largo_plazo_string = "\n".join([f"- {key}: {value}" for key, value in self.memoria_largo_plazo.items()]) or "Ninguno"
        self.estado_animo = max(-5, min(5, self.estado_animo))
        estado_animo_texto = "Neutral"
        if self.estado_animo <= -5: estado_animo_texto = "Crítico"
        elif self.estado_animo < 0: estado_animo_texto = "Negativo"
        elif self.estado_animo >= 3: estado_animo_texto = "Muy Positivo"
        elif self.estado_animo > 0: estado_animo_texto = "Positivo"
        prompt = PROMPT_MAESTRO_ORACULO_V24_LOGICA_ESTRICTA.format(
            estado_animo_texto=f"{estado_animo_texto} ({self.estado_animo})",
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False),
            pregunta_jugador=pregunta_jugador,
            memoria_largo_plazo_string=memoria_largo_plazo_string,
            nombre_secreto=self.personaje_actual_dossier.get("nombre", ""),
            franquicia_secreta=self.personaje_actual_dossier.get("meta_info_franquicia", "")
        )
        raw_response = await self._llamar_a_g4f_robusto(prompt)
        if not raw_response: return {"respuesta": "Dato Ausente", "aclaracion": "Mi mente está... nublada.", "castigo": "ninguno"}
        respuesta_ia = self._extraer_json(raw_response)
        if not respuesta_ia: return {"respuesta": "Dato Ausente", "aclaracion": "Una turbulencia cósmica ha afectado mi visión.", "castigo": "ninguno"}
        if respuesta_ia.get("castigo") == "ninguno" and respuesta_ia.get("respuesta") in ["Sí.", "No."]:
            self.memoria_largo_plazo[pregunta_jugador.capitalize()] = respuesta_ia.get("respuesta")
        castigo = respuesta_ia.get("castigo", "ninguno")
        if castigo == "social": self.estado_animo -= 0.5
        elif castigo == "penalizacion_grave": self.estado_animo -= 3
        elif castigo == "penalizacion_leve": self.estado_animo -= 1
        elif castigo == "ninguno": self.estado_animo += 0.5
        self.estado_animo = max(-5, min(5, self.estado_animo))
        print(f"🧠 Estado de ánimo: {self.estado_animo} | Castigo: {castigo}")
        return respuesta_ia

    def _verificar_adivinanza(self, datos_peticion):
        if not self.personaje_actual_dossier: return {"error": "El juego no se ha iniciado."}
        adivinanza_jugador = datos_peticion.get("adivinanza", "")
        nombre_secreto = self.personaje_actual_dossier.get("nombre", "")
        def normalizar(s):
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower().strip()
        if normalizar(adivinanza_jugador) == normalizar(nombre_secreto):
            return {"resultado": "victoria", "personaje_secreto": self.personaje_actual_dossier}
        else:
            self.estado_animo -= 1
            return {"resultado": "derrota"}

    async def _pedir_sugerencia(self, datos_peticion):
        if not self.personaje_actual_dossier: return {"error": "El juego no ha iniciado."}
        historial_texto = "\n".join(self.memoria_largo_plazo.keys()) or "Ninguna"
        prompt = PROMPT_GENERADOR_SUGERENCIAS_ESTRATEGICO.format(
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False),
            historial_texto=historial_texto
        )
        raw_response = await self._llamar_a_g4f_robusto(prompt)
        if not raw_response: return {"error": "No se pudieron generar sugerencias."}
        respuesta_ia = self._extraer_json(raw_response)
        if not respuesta_ia or "sugerencias" not in respuesta_ia: return {"error": "La IA no generó sugerencias en un formato válido."}
        return respuesta_ia

    def _get_dossiers_existentes(self):
        return [f for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')] if os.path.exists(DOSSIER_PATH) else []
