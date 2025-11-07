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
# CLASE AKINATOR COMPLETA Y DEFINITIVA (v3.2 - You Forzado)

class Akinator:
    def __init__(self):
        # Puedes añadir cualquier inicialización que necesites aquí
        print(f"    - Especialista 'Akinator' (v3.2 - You Forzado) listo.")
        model_info = [f"{model}[{retries}]" for model, retries in [('gpt-4', 5)]]
        print(f"      Cola de modelos y reintentos: {' -> '.join(model_info)}")

    async def _llamar_g4f_con_reintentos_y_respaldo(self, prompt_text, timeout=60):
        # Usamos el proveedor 'You', que es gratuito, fiable y verificado.
        provider_a_usar = g4f.Provider.You
        
        print(f"    ⚙️ [Akinator] Forzando el uso del proveedor: {provider_a_usar.__name__}")
        
        model_priority_list = [('gpt-4', 5)] 

        for model_name, num_retries in model_priority_list:
            for attempt in range(num_retries):
                try:
                    print(f"    >> Akinator: Intentando con '{model_name}' vía {provider_a_usar.__name__} (Intento {attempt + 1}/{num_retries})...")
                    
                    response = await g4f.ChatCompletion.create_async(
                        model=g4f.models.gpt_4,
                        provider=provider_a_usar, # ¡LA LÍNEA CLAVE Y CORRECTA!
                        messages=[{"role": "user", "content": prompt_text}],
                        timeout=timeout
                    )

                    if response and response.strip():
                        print(f"    ✅ Akinator: Éxito con '{model_name}' vía {provider_a_usar.__name__}.")
                        return response
                    raise ValueError("Respuesta inválida o vacía del modelo.")
                except Exception as e:
                    print(f"    ⚠️ Akinator: Falló '{model_name}' en el intento {attempt + 1}. Error: {e}")
                    if attempt < num_retries - 1:
                        await asyncio.sleep(2)
        
        print("    🚨 Akinator: El ciclo interno de llamadas ha fallado.")
        return None

    def _extraer_json(self, texto_crudo):
        # Reutilizamos la misma lógica robusta de extracción de JSON que en Oracle
        if not texto_crudo: return None
        texto_limpio = texto_crudo.strip()
        if texto_limpio.startswith('{{') and texto_limpio.endswith('}}'):
            texto_limpio = texto_limpio[1:-1]
        try:
            json_start = texto_limpio.find('{')
            json_end = texto_limpio.rfind('}') + 1
            if json_start == -1: return None
            json_str = texto_limpio[json_start:json_end]
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        
        # =================================================================
        # ¡OJO! Esta parte es una SIMULACIÓN. 
        # Debes reemplazarla con tus prompts y lógica reales de Akinator.
        # =================================================================
        
        if accion == "iniciar_juego_clasico":
            # Ejemplo: El juego siempre empieza con la misma pregunta
            return {"accion": "Preguntar", "texto": "¿Tu personaje es del sexo masculino?"}
            
        elif accion == "procesar_respuesta_jugador":
            respuesta_jugador = datos_peticion.get("respuesta", "No lo sé")
            
            # Aquí iría tu lógica real:
            # 1. Construir el prompt con el historial de preguntas.
            # 2. Llamar a la IA con: await self._llamar_g4f_con_reintentos_y_respaldo(tu_prompt)
            # 3. Extraer el JSON de la respuesta.
            # 4. Devolver la acción correspondiente (Preguntar, Adivinar, etc.).
            
            # Simulación de respuesta de la IA para que la estructura no se rompa:
            preguntas_siguientes = [
                "¿Tu personaje es de una película?",
                "¿Tu personaje usa un sombrero?",
                "¿Tu personaje es conocido por ser malvado?"
            ]
            
            if random.random() > 0.8: # 20% de probabilidad de intentar adivinar
                return {"accion": "Adivinar", "texto": "Goku"}
            else:
                return {"accion": "Preguntar", "texto": random.choice(preguntas_siguientes)}

        return {"error": f"Acción '{accion}' no reconocida en Akinator."}

