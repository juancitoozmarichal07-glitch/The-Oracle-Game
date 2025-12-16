import g4f
import asyncio
import json
import random
import os
import unicodedata
import re
import time
from difflib import SequenceMatcher

# --- CONFIGURACIÓN ---
DOSSIER_PATH = os.path.join(os.path.dirname(__file__), '..', 'dossiers')

# --- PERSONAJE DE EMERGENCIA ---
SHERLOCK_HOLMES_DOSSIER = {
    "nombre": "Sherlock Holmes",
    "es_real": False,
    "genero": "Masculino",
    "especie": "Humano",
    "universo_o_epoca": "Inglaterra Victoriana",
    "meta_info_franquicia": "Saga de libros de Arthur Conan Doyle",
    "rol_principal": "Detective consultor",
    "arquetipo": "El Detective Genio",
    "personalidad_clave": "Observador, lógico, excéntrico",
    "habilidad_principal": "Deducción",
    "debilidad_notable": "Aburrimiento sin un caso"
}

# --- PROMPTS ---
PROMPT_MAESTRO_ORACULO = """<constitution>
<identity>You are a cosmic Oracle.</identity>
<response_protocol>
Answer only with:
"Sí.", "No.", "Probablemente sí.", "Probablemente no.", "Los datos son confusos."
</response_protocol>
<sacred_name_clause>NEVER mention the character's name ("{nombre_secreto}").</sacred_name_clause>
</constitution>
<context>
<secret_dossier>{dossier_string}</secret_dossier>
<long_term_memory>{memoria_largo_plazo_string}</long_term_memory>
<user_input>{pregunta_jugador}</user_input>
</context>
<mandatory_json_response_format>{{{{ "respuesta": "...", "aclaracion": "...", "castigo": "ninguno" }}}}</mandatory_json_response_format>
"""

PROMPT_CREADOR_DOSSIER = """You are an archivist. Generate a JSON dossier in Spanish.
<mandatory_json_response_format>
{{{{ "nombre": "...", "es_real": false, "genero": "...", "especie": "...",
"universo_o_epoca": "...", "meta_info_franquicia": "...",
"rol_principal": "...", "arquetipo": "...",
"personalidad_clave": "...", "habilidad_principal": "...",
"debilidad_notable": "..." }}}}
</mandatory_json_response_format>
"""

PROMPT_PENSADOR_ALEATORIO = """Pick a well-known character NOT in this list:
{existing_list}
Return only JSON:
{{ "character_name": "..." }}
"""

PROMPT_GENERADOR_SUGERENCIAS = """Generate 5 strategic yes/no questions.
Return JSON:
{{ "sugerencias": ["¿...?", "..."] }}
"""

# --- CLASE ORACLE ---
class Oracle:
    def __init__(self):
        self.personaje_actual_dossier = None
        self.model = 'gpt-4'

        if not os.path.exists(DOSSIER_PATH):
            os.makedirs(DOSSIER_PATH)

        print("🧠 Oracle v31.0 STABLE listo.")

    # ---------- UTILIDADES ----------
    async def _llamar_ia(self, prompt):
        try:
            return await g4f.ChatCompletion.create_async(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=30
            )
        except:
            return None

    def _extraer_json(self, texto):
        if not texto:
            return None
        try:
            start = texto.find('{')
            end = texto.rfind('}') + 1
            return json.loads(texto[start:end])
        except:
            return None

    def _normalizar_archivo(self, nombre):
        nombre = ''.join(
            c for c in unicodedata.normalize('NFD', nombre)
            if unicodedata.category(c) != 'Mn'
        )
        return nombre.lower().replace(' ', '_') + '.json'

    def _normalizar(self, texto):
        if not isinstance(texto, str):
            return ""
        texto = ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
        return re.sub(r'[^a-z0-9]', '', texto.lower())

    # ---------- CORE ----------
    async def ejecutar(self, datos_peticion):
        accion = datos_peticion.get("accion")
        acciones = {
            "iniciar_juego": self._iniciar_juego,
            "procesar_pregunta": self._procesar_pregunta,
            "verificar_adivinanza": self._verificar_adivinanza,
            "pedir_sugerencia": self._pedir_sugerencia
        }
        return await acciones.get(accion, self._accion_invalida)(datos_peticion)

    async def _accion_invalida(self, _):
        return {"error": "Acción no reconocida."}

    # ---------- JUEGO ----------
    async def _iniciar_juego(self, _=None):
        dossiers = [f for f in os.listdir(DOSSIER_PATH) if f.endswith('.json')]

        for _ in range(3):
            prompt = PROMPT_PENSADOR_ALEATORIO.format(existing_list=", ".join(dossiers))
            nombre_raw = await self._llamar_ia(prompt)
            nombre_json = self._extraer_json(nombre_raw)
            if not nombre_json:
                continue

            nombre = nombre_json["character_name"]
            dossier_raw = await self._llamar_ia(
                PROMPT_CREADOR_DOSSIER.format(character_name=nombre)
            )
            dossier = self._extraer_json(dossier_raw)
            if dossier:
                path = os.path.join(DOSSIER_PATH, self._normalizar_archivo(dossier["nombre"]))
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(dossier, f, ensure_ascii=False, indent=2)
                self.personaje_actual_dossier = dossier
                return {"status": "ok", "personaje_secreto": dossier}

        if dossiers:
            with open(os.path.join(DOSSIER_PATH, random.choice(dossiers)), 'r', encoding='utf-8') as f:
                self.personaje_actual_dossier = json.load(f)
        else:
            self.personaje_actual_dossier = SHERLOCK_HOLMES_DOSSIER

        return {"status": "ok", "personaje_secreto": self.personaje_actual_dossier}

    async def _procesar_pregunta(self, datos):
        if not self.personaje_actual_dossier:
            return {"respuesta": "Los datos son confusos.", "aclaracion": "", "castigo": "ninguno"}

        prompt = PROMPT_MAESTRO_ORACULO.format(
            dossier_string=json.dumps(self.personaje_actual_dossier, ensure_ascii=False),
            memoria_largo_plazo_string="",
            pregunta_jugador=datos.get("pregunta", ""),
            nombre_secreto=self.personaje_actual_dossier["nombre"]
        )
        raw = await self._llamar_ia(prompt)
        return self._extraer_json(raw) or {"error": "IA falló."}

    async def _verificar_adivinanza(self, datos):
        guess = self._normalizar(datos.get("adivinanza", ""))
        secreto = self._normalizar(self.personaje_actual_dossier["nombre"])

        if guess and (guess in secreto or secreto in guess):
            return {"resultado": "victoria", "personaje_secreto": self.personaje_actual_dossier}

        similitud = SequenceMatcher(None, guess, secreto).ratio()
        if similitud >= 0.80:
            return {"resultado": "victoria", "personaje_secreto": self.personaje_actual_dossier}

        return {"resultado": "derrota", "personaje_secreto": self.personaje_actual_dossier}

    async def _pedir_sugerencia(self, datos):
        raw = await self._llamar_ia(PROMPT_GENERADOR_SUGERENCIAS)
        return self._extraer_json(raw) or {"error": "No hay sugerencias."}
