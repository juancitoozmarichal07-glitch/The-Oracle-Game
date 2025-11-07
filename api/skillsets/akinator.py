# skillsets/akinator.py - v2.6 (Estructura Unificada por Manus)
# CORRECCIÓN: Se unifican todos los métodos en una sola definición de clase
# y se refactoriza el método `ejecutar` para que sea el único punto de entrada.

import g4f
import asyncio
import json
import re

# --- PROMPTS DE IA (SIN CAMBIOS) ---
PROMPT_INICIAR_JUEGO = """
<task>You are a game master like the classic game "Akinator". Your goal is to guess the character the user is thinking of by asking a series of Yes/No questions.</task>
<instruction>
You are about to ask your very first question. To start the game efficiently, your first question MUST be about the character's reality.
Follow these strict rules:
1.  Your question must be one of these two, exactly: "¿Tu personaje es una persona real?" or "¿Tu personaje es ficticio?". Choose one.
2.  Your response MUST be a single, valid JSON object following this exact format.
</instruction>
<mandatory_json_response_format>
{{
  "accion": "Preguntar",
  "texto": "Your chosen first question in Spanish"
}}
</mandatory_json_response_format>
"""

# --- REEMPLAZA ESTE PROMPT EN AKINATOR.PY ---
# En akinator.py

PROMPT_PROCESAR_RESPUESTA_DEEP_THINK = """
<task>
You are a master detective game master (like Akinator). Your goal is to deduce the character the user is thinking of.
</task>

<context>
    <game_state>
    {estado_juego_string}
    </game_state>
    <deduction_journal>
    {diario_de_deduccion}
    </deduction_journal>
</context>

<instruction>
1.  **Analyze the user's latest answer.** Your primary goal is to write a brief, internal "Deep Think" monologue **IN SPANISH**.
    - **CRITICAL RULE:** Your "Deep Think" MUST be a single, concise sentence or a list of keywords. Be efficient.
    - **Example of a good Spanish Deep Think:** "Deducción: Ficticio, tiene poderes. Próximo paso: Determinar medio (cómic, película, etc.)."
    - **CRITICAL:** If the user's answer is ambiguous (e.g., "Probably Yes. But..."), your "Deep Think" MUST focus on the user's clarification.

2.  **Decide your next move.** You have two options:

    *   **A) Ask a Question:** If you need more information, formulate a new, strategic YES/NO question. This is your standard move.
        - **ABSOLUTE LAW:** Your question MUST be a simple, direct, YES/NO question. Strictly no "A or B" questions.
        - **JSON ACTION:** `Preguntar`

    *   **B) Make a Guess:** If you are **extremely confident (95% or more)**, you MUST guess the character's name.
        - **THE CAUTION PRINCIPLE:** It is better to ask one more question than to guess wrong. Do not guess a category or a description. Only guess a specific, proper name.
        - **JSON ACTION:** `Adivinar`

3.  **Construct your JSON response.** Based on your choice above, create the JSON.
</instruction>

<json_formats>
// Option A
{{
  "deep_think": "Un resumen muy corto, en una frase, de tus pensamientos en español.",
  "accion": "Preguntar",
  "texto": "A simple Yes/No question in Spanish."
}}
// Option B
{{
  "deep_think": "La deducción final apunta a un solo personaje.",
  "accion": "Adivinar",
  "texto": "The character's proper name (e.g., 'Bart Simpson', 'Darth Vader')."
}}
</json_formats>
"""



class Akinator:
    def __init__(self):
        self.historial = []
        # --- AJUSTE: Solo gpt-4 con 5 reintentos ---
        self._model_priority_list = [('gpt-4', 5)]
        
        print(f"    - Especialista 'Akinator' (v2.7 - Resiliencia Total) listo.")
        model_info = [f"{model}[{retries}]" for model, retries in self._model_priority_list]
        print(f"      Cola de modelos y reintentos: {' -> '.join(model_info)}")

    # Pega esta función en tu akinator.py (reemplazando la que ya tengas para llamar a g4f)
async def _llamar_g4f_con_reintentos_y_respaldo(self, prompt_text, timeout=60):
    print(f"    ⚙️ [Akinator] Forzando el uso del proveedor: g4f.Provider.Bing")
    
    # Si no tienes una lista de modelos en Akinator, puedes definir una simple aquí
    model_priority_list = [('gpt-4', 5)] 

    for model_name, num_retries in model_priority_list:
        for attempt in range(num_retries):
            try:
                print(f"    >> Akinator: Intentando con '{model_name}' vía Bing (Intento {attempt + 1}/{num_retries})...")
                
                response = await g4f.ChatCompletion.create_async(
                    model=g4f.models.gpt_4,
                    provider=g4f.Provider.Bing,
                    messages=[{"role": "user", "content": prompt_text}],
                    timeout=timeout
                )

                if response and response.strip():
                    print(f"    ✅ Akinator: Éxito con '{model_name}' vía Bing.")
                    return response
                raise ValueError("Respuesta inválida o vacía del modelo.")
            except Exception as e:
                print(f"    ⚠️ Akinator: Falló '{model_name}' en el intento {attempt + 1}. Error: {e}")
                if attempt < num_retries - 1:
                    await asyncio.sleep(2)
    
    print("    🚨 Akinator: El ciclo interno de llamadas ha fallado.")
    return None


    def _extraer_json(self, texto_crudo):
        if not texto_crudo:
            return None
        
        # Lógica de limpieza de dobles llaves, por si acaso.
        texto_limpio = texto_crudo.strip()
        if texto_limpio.startswith('{{') and texto_limpio.endswith('}}'):
            print("    🔧 Akinator: Detectadas dobles llaves. Corrigiendo formato...")
            texto_limpio = texto_limpio[1:-1]

        try:
            json_start = texto_limpio.find('{')
            json_end = texto_limpio.rfind('}') + 1
            if json_start == -1: return None
            return json.loads(texto_limpio[json_start:json_end])
        except json.JSONDecodeError as e:
            print(f"    ⚠️ JSON fallido. Error: {e}. Intentando auto-corrección...")
            pattern = re.compile(r'("deep_think"\s*:\s*".*?")\s*("accion"\s*:)')
            texto_corregido = pattern.sub(r'\1,\n\2', texto_limpio)

            if texto_corregido != texto_limpio:
                try:
                    print("    ✅ ¡Auto-corrección aplicada! Procesando JSON reparado.")
                    json_start = texto_corregido.find('{')
                    json_end = texto_corregido.rfind('}') + 1
                    return json.loads(texto_corregido[json_start:json_end])
                except Exception as e2:
                    print(f"    🚨 La auto-corrección también falló. Error: {e2}")
                    return None
            else:
                print("    🚨 No se pudo aplicar la auto-corrección.")
                return None

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        
        if accion == "iniciar_juego_clasico":
            return await self._iniciar_juego_clasico()
        elif accion == "procesar_respuesta_jugador":
            return await self._procesar_respuesta_jugador(datos_peticion)
        
        return {"error": f"Acción '{accion}' no reconocida por Akinator."}

    async def _iniciar_juego_clasico(self):
        self.historial = []
        tiempo_de_enfriamiento = 15
        intento_ciclo = 0

        while True:
            intento_ciclo += 1
            print(f"    [Akinator Inicio] Iniciando ciclo de IA #{intento_ciclo}...")
            
            raw_response = await self._llamar_a_g4f_robusto(PROMPT_INICIAR_JUEGO)
            if raw_response:
                json_response = self._extraer_json(raw_response)
                if json_response and json_response.get("accion") == "Preguntar":
                    self.historial.append(f"IA preguntó: '{json_response.get('texto')}'")
                    print("    ✅ ¡Éxito! Primera pregunta generada.")
                    return json_response
            
            print(f"    🚨 El ciclo de inicio #{intento_ciclo} ha fallado.")
            print(f"    ❄️ Enfriando durante {tiempo_de_enfriamiento} segundos antes de reintentar...")
            await asyncio.sleep(tiempo_de_enfriamiento)

    async def _procesar_respuesta_jugador(self, datos_peticion):
        respuesta_jugador = datos_peticion.get("respuesta")
        estado_juego = datos_peticion.get("estado_juego", {})
        tiempo_de_enfriamiento = 15
        
        if not respuesta_jugador:
            return {"error": "No se recibió respuesta del jugador."}
        
        if respuesta_jugador.startswith("No, no es"):
            self.historial.append(f"Jugador me corrigió: '{respuesta_jugador}'. Mi anterior adivinanza fue errónea.")
        else:
            self.historial.append(f"Jugador respondió: '{respuesta_jugador}'")
        
        diario_texto = "\n".join(self.historial)
        prompt = PROMPT_PROCESAR_RESPUESTA_DEEP_THINK.format(
            diario_de_deduccion=diario_texto,
            estado_juego_string=json.dumps(estado_juego)
        )
        
        intento_ciclo = 0
        while True:
            intento_ciclo += 1
            print(f"    [Akinator Pregunta] Iniciando ciclo de IA #{intento_ciclo}...")
            
            raw_response = await self._llamar_a_g4f_robusto(prompt)
            if raw_response:
                json_response = self._extraer_json(raw_response)
                if json_response:
                    deep_think = json_response.get("deep_think", "(No se pudo generar un pensamiento)")
                    accion = json_response.get("accion")
                    print(f"    🧠 Akinator Deep Think: {deep_think}")
                    
                    self.historial.append(f"IA Deep Think: '{deep_think}'")

                    if accion == "Preguntar":
                        self.historial.append(f"IA preguntó: '{json_response.get('texto')}'")
                    elif accion == "Comentar_y_Preguntar":
                        self.historial.append(f"IA comentó: '{json_response.get('comentario')}'")
                        self.historial.append(f"IA preguntó: '{json_response.get('pregunta')}'")
                    
                    print("    ✅ ¡Éxito! Respuesta de IA procesada.")
                    return json_response
            
            print(f"    🚨 El ciclo de pregunta #{intento_ciclo} ha fallado.")
            print(f"    ❄️ Enfriando durante {tiempo_de_enfriamiento} segundos antes de reintentar...")
            await asyncio.sleep(tiempo_de_enfriamiento)
