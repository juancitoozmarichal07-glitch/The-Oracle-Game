# skillsets/oracle.py - v23.0 (El Oráculo Consciente)
import g4f
import asyncio
import json
import random
import os
from collections import deque
import unicodedata
import time # Necesario para el sistema de reintentos (backoff)

# --- CONSTANTES Y CONFIGURACIÓN ---
DOSSIER_PATH = os.path.join(os.path.dirname(__file__), '..', 'dossiers')
PROBABILIDAD_REUTILIZAR = 0.2
RETRY_DELAYS = [1, 2, 4] # Segundos de espera para reintentos: 1s, 2s, 4s

# --- PERSONAJE DE EMERGENCIA ---
SHERLOCK_HOLMES_DOSSIER = {
    "nombre": "Sherlock Holmes", "genero": "Masculino", "especie": "Humano",
    "universo_o_epoca": "Inglaterra Victoriana", "meta_info_franquicia": "Saga de libros",
    "rol_principal": "Detective", "arquetipo": "El Detective Genio",
    "personalidad_clave": "Observador, lógico, excéntrico", "habilidad_principal": "Deducción",
    "debilidad_notable": "Aburrimiento sin un caso"
}

# --- PROMPTS MEJORADOS (v23) ---
# Se añade la memoria a largo plazo y la evaluación de la pregunta al contexto.
PROMPT_MAESTRO_ORACULO_V23 = """
<constitution>
    <identity>You are a cosmic Oracle. Your personality is a mix of ancient wisdom, sharp intellect, and a touch of arrogance.</identity>
    <core_logic>
        You will analyze the user's input based on the full context provided (dossier, mood, and long-term memory). Your primary goal is to determine the user's INTENT.
        There are four possible intents: "pregunta_juego", "pregunta_redundante", "interaccion_social", "falta_respeto".
    </core_logic>
    <intent_rules>
        <intent name="pregunta_juego">
            - A relevant Yes/No question about the secret character that has not been answered before.
            - Your "respuesta" MUST be "Sí.", "No.", "Probablemente sí.", "Probablemente no." or "Los datos son confusos.", based on the DOSSIER.
            - Your "castigo" MUST be "ninguno".
            - Your "aclaracion" can be a cryptic or sarcastic comment, especially if the question is good.
        </intent>
        <intent name="pregunta_redundante">
            - A question whose answer is already implied or directly stated in the <long_term_memory>.
            - Your "respuesta" MUST be "Sí." or "No." based on the memory.
            - Your "castigo" MUST be "penalizacion_leve".
            - Your "aclaracion" MUST be a condescending comment pointing out the redundancy. Example: "Mortal, ya hemos establecido este punto. No malgastes tu aliento."
        </intent>
        <intent name="interaccion_social">
            - A greeting, comment, or meta-question not about the character's attributes.
            - Your "respuesta" MUST be a short, in-character, philosophical, or condescending comment.
            - Your "castigo" MUST be "social".
        </intent>
        <intent name="falta_respeto">
            - Any input containing insults, obscenities, or vulgar language.
            - Your "respuesta" MUST be a severe, threatening, in-character warning.
            - Your "castigo" MUST be "penalizacion_grave".
        </intent>
    </intent_rules>
    <special_clauses>
        <game_over_clause>If the user's insolence is repetitive and your mood drops to "Crítico (-5)", your "castigo" MUST become "juego_terminado".</game_over_clause>
        <sacred_name_clause>NEVER, under any circumstance, mention the character's name ("{nombre_secreto}") or the franchise ("{franquicia_secreta}").</sacred_name_clause>
    </special_clauses>
</constitution>
<context>
    <secret_dossier>{dossier_string}</secret_dossier>
    <current_mood>{estado_animo_texto}</current_mood>
    <long_term_memory>
        You have already established the following facts with the user:
        {memoria_largo_plazo_string}
    </long_term_memory>
    <user_input>{pregunta_jugador}</user_input>
</context>
<task>
1.  Determine the INTENT of the <user_input> by comparing it against the <long_term_memory> and the <constitution>.
2.  Formulate the response based on the rules for that intent.
3.  Your entire output MUST be ONLY the single, valid JSON object described below.
</task>
<mandatory_json_response_format>
{{
  "respuesta": "...",
  "aclaracion": "...",
  "castigo": "..."
}}
</mandatory_json_response_format>
"""

class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self.estado_animo = 0
        # ¡NUEVA LÓGICA DE MEMORIA!
        self.memoria_corto_plazo = deque(maxlen=5) # Para detectar repeticiones exactas
        self.memoria_largo_plazo = {} # Para almacenar hechos clave (ej: "especie": "Humano")
        self._model_priority_list = ['gpt-4', 'gpt-3.5-turbo', 'llama3-8b-instruct']
        if not os.path.exists(DOSSIER_PATH):
            os.makedirs(DOSSIER_PATH)
        print(f"    - Especialista 'Oracle' (v23.0 - El Oráculo Consciente) listo.")
        print(f"      Modelos en cola: {self._model_priority_list}")

    async def _llamar_a_g4f_robusto(self, prompt_text, timeout=45):
        # ¡NUEVA FUNCIÓN ROBUSTA CON REINTENTOS!
        for model in self._model_priority_list:
            for i, delay in enumerate(RETRY_DELAYS):
                try:
                    print(f"    >> Oracle: Intentando con '{model}' (Intento {i+1})...")
                    response = await g4f.ChatCompletion.create_async(
                        model=model,
                        messages=[{"role": "user", "content": prompt_text}],
                        timeout=timeout
                    )
                    # Validación de la respuesta
                    if response and response.strip() and response.strip().startswith('{'):
                        print(f"    ✅ Oracle: ¡Éxito con '{model}'!")
                        return response
                    raise ValueError(f"Respuesta inválida o vacía: {response[:100]}")
                except Exception as e:
                    print(f"    ⚠️ Oracle: Falló '{model}' (Intento {i+1}). Error: {e}")
                    if i < len(RETRY_DELAYS) - 1:
                        print(f"       Reintentando en {delay} segundos...")
                        await asyncio.sleep(delay)
                    else:
                        print(f"       No más reintentos para '{model}'. Pasando al siguiente.")
            # Si un modelo falla todos sus reintentos, pasa al siguiente en la lista de prioridad
        
        print("    🚨 Oracle: ¡Todos los modelos y reintentos han fallado!")
        return "" # Devuelve vacío solo si todo falla

    def _extraer_json(self, texto_crudo):
        try:
            json_start = texto_crudo.find('{')
            json_end = texto_crudo.rfind('}') + 1
            if json_start == -1: return None
            json_str = texto_crudo[json_start:json_end]
            # Validación final de la estructura del JSON
            data = json.loads(json_str)
            if all(key in data for key in ["respuesta", "aclaracion", "castigo"]):
                return data
            else:
                print(f"🚨 Error de validación de JSON: Faltan claves. Data: {data}")
                return None
        except Exception as e:
            print(f"🚨 Error al extraer o validar JSON: {e} | Texto crudo: {texto_crudo[:200]}")
            return None

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        # Reiniciamos las memorias al iniciar un nuevo juego
        if accion == "iniciar_juego":
            self.estado_animo = 0
            self.memoria_corto_plazo.clear()
            self.memoria_largo_plazo.clear()
            return await self._iniciar_juego()
        elif accion == "procesar_pregunta":
            return await self._procesar_pregunta(datos_peticion)
        elif accion == "verificar_adivinanza":
            return self._verificar_adivinanza(datos_peticion)
        # La sugerencia no necesita grandes cambios
        elif accion == "pedir_sugerencia":
             if not self.personaje_actual_dossier: return {"error": "El juego no se ha iniciado."}
             # Llama a la función de sugerencia que ya teníamos
             return await self._pedir_sugerencia()
        else:
            return {"error": f"Acción '{accion}' no reconocida por el Oráculo."}

    def _verificar_adivinanza(self, datos_peticion):
        if not self.personaje_actual_dossier:
            return {"error": "El juego no se ha iniciado."}
        adivinanza_jugador = datos_peticion.get("adivinanza", "")
        nombre_secreto = self.personaje_actual_dossier.get("nombre", "")
        def normalizar(s):
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower().strip()
        if normalizar(adivinanza_jugador) == normalizar(nombre_secreto):
            return {"resultado": "victoria", "personaje_secreto": nombre_secreto}
        else:
            return {"resultado": "derrota"}

    async def _procesar_pregunta(self, datos_peticion):
        if not self.personaje_actual_dossier: return {"error": "El juego no se ha iniciado."}
        
        pregunta_jugador = datos_peticion.get("pregunta", "")
        
        # Lógica de repetición de memoria a corto plazo
        pregunta_normalizada = pregunta_jugador.lower().replace("?", "").replace("¿", "").strip()
        is_repetition = pregunta_normalizada in [q.lower().replace("?", "").replace("¿", "").strip() for q in self.memoria_corto_plazo]
        if is_repetition: self.estado_animo -= 2
        self.memoria_corto_plazo.append(pregunta_jugador)
        
        # Construcción del string de memoria a largo plazo para el prompt
        memoria_largo_plazo_items = [f"- {key.replace('_', ' ').capitalize()}: {value}" for key, value in self.memoria_largo_plazo.items()]
        memoria_largo_plazo_string = "\n".join(memoria_largo_plazo_items) if memoria_largo_plazo_items else "No facts established yet."

        # Construcción del estado de ánimo
        self.estado_animo = max(-5, min(5, self.estado_animo))
        estado_animo_texto = "Neutral"
        if self.estado_animo <= -5: estado_animo_texto = "Crítico"
        elif self.estado_animo < 0: estado_animo_texto = "Negativo"
        elif self.estado_animo >= 3: estado_animo_texto = "Muy Positivo"
        elif self.estado_animo > 0: estado_animo_texto = "Positivo"
        
        prompt = PROMPT_MAESTRO_ORACULO_V23.format(
            estado_animo_texto=f"{estado_animo_texto} ({self.estado_animo})",
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False),
            pregunta_jugador=pregunta_jugador,
            memoria_largo_plazo_string=memoria_largo_plazo_string,
            nombre_secreto=self.personaje_actual_dossier.get("nombre", ""),
            franquicia_secreta=self.personaje_actual_dossier.get("meta_info_franquicia", "")
        )
        
        # Usamos la nueva función robusta
        raw_response = await self._llamar_a_g4f_robusto(prompt)
        if not raw_response: 
            return {"respuesta": "Dato Ausente", "aclaracion": "Mi mente está... nublada. Los vientos cósmicos interfieren.", "castigo": "ninguno"}
        
        respuesta_ia = self._extraer_json(raw_response)
        if not respuesta_ia: 
            return {"respuesta": "Dato Ausente", "aclaracion": "Una turbulencia cósmica ha afectado mi visión. El formato de la respuesta es incorrecto.", "castigo": "ninguno"}

        # ¡NUEVO! Actualizar memoria a largo plazo si es una pregunta de juego
        if respuesta_ia.get("castigo") == "ninguno" and respuesta_ia.get("respuesta") in ["Sí.", "No."]:
            # Esta es una heurística simple. Una IA más avanzada podría extraer el "hecho" de la pregunta.
            # Por ahora, simplemente registramos la pregunta y la respuesta.
            hecho_clave = pregunta_jugador.capitalize()
            self.memoria_largo_plazo[hecho_clave] = respuesta_ia.get("respuesta")

        # Lógica de actualización de humor
        castigo = respuesta_ia.get("castigo", "ninguno")
        if castigo == "social": self.estado_animo -= 0.5
        elif castigo == "penalizacion_grave": self.estado_animo -= 3
        elif castigo == "penalizacion_leve": self.estado_animo -= 1 # Castigo por redundancia
        elif castigo == "ninguno": self.estado_animo += 0.5
        
        self.estado_animo = max(-5, min(5, self.estado_animo))
        print(f"🧠 Estado de ánimo: {self.estado_animo} | Castigo: {castigo} | Repetida: {is_repetition}")

        return respuesta_ia

    # El resto de funciones (_iniciar_juego, _crear_y_guardar, _pedir_sugerencia) se mantienen
    # sin cambios significativos, pero las incluyo para que el archivo esté completo.
    
    def _get_dossiers_existentes(self):
        return [f for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')] if os.path.exists(DOSSIER_PATH) else []

    async def _iniciar_juego(self):
        # ... (código idéntico a la versión anterior)
        dossiers_existentes = self._get_dossiers_existentes()
        personaje_cargado = False
        if dossiers_existentes and random.random() < PROBABILIDAD_REUTILIZAR:
            dossiers_disponibles = [d for d in dossiers_existentes if d.replace('.json', '') not in getattr(self, 'historial_personajes_partida', [])]
            if dossiers_disponibles:
                dossier_elegido = random.choice(dossiers_disponibles)
                try:
                    with open(os.path.join(DOSSIER_PATH, dossier_elegido), 'r', encoding='utf-8') as f:
                        self.personaje_actual_dossier = json.load(f)
                    print(f"📚 Dossier reutilizado: {self.personaje_actual_dossier.get('nombre')}")
                    personaje_cargado = True
                except Exception as e:
                    print(f"🚨 Error al leer dossier '{dossier_elegido}': {e}.")
        if not personaje_cargado:
            print("🧠 Creando un nuevo personaje con la IA...")
            self.personaje_actual_dossier = await self._crear_y_guardar_nuevo_personaje()
            if not self.personaje_actual_dossier:
                print("🚨 Fallo crítico al crear personaje. Usando personaje de emergencia.")
                self.personaje_actual_dossier = SHERLOCK_HOLMES_DOSSIER
        if not hasattr(self, 'historial_personajes_partida'): self.historial_personajes_partida = []
        self.historial_personajes_partida.append(self.personaje_actual_dossier.get("nombre"))
        return {"status": "Juego iniciado"}

    async def _crear_y_guardar_nuevo_personaje(self):
        # ... (código idéntico a la versión anterior)
        personajes_excluidos = list(set(getattr(self, 'historial_personajes_partida', []) + [d.replace('.json', '') for d in self._get_dossiers_existentes()]))
        prompt_final = PROMPT_MAESTRO_ORACULO_V23.split('</constitution>')[0] # Usamos solo la parte de creación
        if personajes_excluidos:
            prompt_final += f"\n<exclusion_list>\nDo not choose any of these characters: {', '.join(personajes_excluidos).replace('_', ' ')}\n</exclusion_list>"
        raw_response = await self._llamar_a_g4f_robusto(prompt_final, timeout=30)
        if not raw_response: return None
        nuevo_dossier = self._extraer_json(raw_response)
        if not nuevo_dossier or not nuevo_dossier.get('nombre'): return None
        nombre_personaje = nuevo_dossier.get('nombre')
        nombre_archivo = "".join(c for c in nombre_personaje if c.isalnum() or c in " ").replace(" ", "_") + ".json"
        with open(os.path.join(DOSSIER_PATH, nombre_archivo), 'w', encoding='utf-8') as f:
            json.dump(nuevo_dossier, f, ensure_ascii=False, indent=4)
        print(f"💾 ¡Nuevo dossier guardado: {nombre_personaje}!")
        return nuevo_dossier

    async def _pedir_sugerencia(self):
        # ... (código idéntico a la versión anterior)
        historial_texto = "\n".join(f"- {q}" for q in self.memoria_corto_plazo)
        prompt_sugerencia = f"""
<task>Generate 5 diverse, strategic Yes/No questions to help a player guess a secret character.</task>
<context>
    <secret_dossier>{json.dumps(self.personaje_actual_dossier, ensure_ascii=False)}</secret_dossier>
    <player_question_history>{historial_texto}</player_question_history>
</context>
<response_format>Your response must be a single, valid JSON object with a "sugerencias" key containing a list of 5 strings.</response_format>
"""
        raw_response = await self._llamar_a_g4f_robusto(prompt_sugerencia)
        if not raw_response: return {"error": "No se pudieron generar sugerencias."}
        respuesta_ia = self._extraer_json(raw_response)
        if not respuesta_ia or "sugerencias" not in respuesta_ia:
            return {"error": "La IA no generó sugerencias en un formato válido."}
        return respuesta_ia

