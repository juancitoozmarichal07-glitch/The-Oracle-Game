#!/usr/bin/env python3
"""
THE ORACLE - Backend HÍBRIDO COMPLETO
Versión: 50 personajes + Dashboard + Sugerencias + Pistas
- ✅ Carga personajes desde personajes.json (ruta absoluta)
- ✅ Analizador con cobertura de 60+ patrones
- ✅ Dashboard interactivo con métricas
- ✅ Sugerencias inteligentes
- ✅ Sistema de huecos y errores
- ✅ Exportación TXT
"""

from flask import Flask, request, jsonify, render_template_string, send_file, make_response
from flask_cors import CORS
from io import BytesIO, StringIO
from collections import Counter, defaultdict
import random
import unicodedata
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

app = Flask(__name__)
CORS(app)

# ===================================================================
# CONFIGURACIÓN
# ===================================================================

REGISTRO_HUECOS_FILE = "huecos_diccionario.json"
METRICAS_FILE = "metricas_oracle.json"
PERSONAJES_FILE = "personajes.json"
MAX_PREGUNTAS = 20


# ===================================================================
# CARGADOR DE PERSONAJES (RUTA ABSOLUTA)
# ===================================================================

def cargar_personajes(archivo: str = PERSONAJES_FILE) -> List[Dict]:
    """
    Carga personajes desde archivo JSON externo.
    Busca en el MISMO directorio donde está este script.
    """
    try:
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_completa = os.path.join(directorio_actual, archivo)

        if os.path.exists(ruta_completa):
            with open(ruta_completa, 'r', encoding='utf-8') as f:
                data = json.load(f)
                personajes = data.get('personajes', [])
                print(f"✅ {len(personajes)} personajes cargados desde {ruta_completa}")
                return personajes
        else:
            print(f"⚠️  Archivo {ruta_completa} no encontrado")
            print(f"📁 Directorio actual: {os.getcwd()}")
            print(f"📁 Archivos en el directorio: {os.listdir('.')}")
            return []
    except Exception as e:
        print(f"❌ Error cargando personajes: {e}")
        return []

PERSONAJES = cargar_personajes()

if not PERSONAJES:
    print("=" * 60)
    print("⚠️  ADVERTENCIA: No se cargaron personajes")
    print("Asegúrate de que personajes.json existe en el mismo directorio")
    print("=" * 60)


# ===================================================================
# SISTEMA DE MÉTRICAS
# ===================================================================

class MetricasManager:
    def __init__(self):
        self.metricas = self.cargar_metricas()

    def cargar_metricas(self) -> Dict:
        if os.path.exists(METRICAS_FILE):
            try:
                with open(METRICAS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "partidas_totales": 0,
            "partidas_ganadas": 0,
            "partidas_perdidas": 0,
            "preguntas_totales": 0,
            "personajes_usados": {},
            "preguntas_frecuentes": {},
            "huecos_por_categoria": {},
            "tasa_exito_por_personaje": {},
            "errores": []
        }

    def guardar_metricas(self):
        try:
            with open(METRICAS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.metricas, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error guardando métricas: {e}")

    def registrar_partida_iniciada(self, personaje: str):
        self.metricas["partidas_totales"] += 1
        if personaje not in self.metricas["personajes_usados"]:
            self.metricas["personajes_usados"][personaje] = 0
        self.metricas["personajes_usados"][personaje] += 1
        self.guardar_metricas()

    def registrar_pregunta(self, pregunta: str):
        self.metricas["preguntas_totales"] += 1
        pregunta_key = pregunta.lower()[:100]
        if pregunta_key not in self.metricas["preguntas_frecuentes"]:
            self.metricas["preguntas_frecuentes"][pregunta_key] = 0
        self.metricas["preguntas_frecuentes"][pregunta_key] += 1
        self.guardar_metricas()

    def registrar_resultado(self, personaje: str, ganado: bool):
        if ganado:
            self.metricas["partidas_ganadas"] += 1
        else:
            self.metricas["partidas_perdidas"] += 1
        if personaje not in self.metricas["tasa_exito_por_personaje"]:
            self.metricas["tasa_exito_por_personaje"][personaje] = {"ganadas": 0, "perdidas": 0}
        if ganado:
            self.metricas["tasa_exito_por_personaje"][personaje]["ganadas"] += 1
        else:
            self.metricas["tasa_exito_por_personaje"][personaje]["perdidas"] += 1
        self.guardar_metricas()

    def registrar_hueco_categoria(self, categoria: str):
        if categoria not in self.metricas["huecos_por_categoria"]:
            self.metricas["huecos_por_categoria"][categoria] = 0
        self.metricas["huecos_por_categoria"][categoria] += 1
        self.guardar_metricas()

    def registrar_error(self, error: str, contexto: str = ""):
        self.metricas["errores"].append({
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "contexto": contexto
        })
        if len(self.metricas["errores"]) > 100:
            self.metricas["errores"] = self.metricas["errores"][-100:]
        self.guardar_metricas()

    def obtener_estadisticas(self) -> Dict:
        total = self.metricas["partidas_totales"]
        ganadas = self.metricas["partidas_ganadas"]
        return {
            "partidas_totales": total,
            "partidas_ganadas": ganadas,
            "partidas_perdidas": self.metricas["partidas_perdidas"],
            "tasa_victoria": round(ganadas / total * 100, 2) if total > 0 else 0,
            "preguntas_totales": self.metricas["preguntas_totales"],
            "promedio_preguntas": round(self.metricas["preguntas_totales"] / total, 2) if total > 0 else 0,
            "personajes_mas_usados": sorted(
                self.metricas["personajes_usados"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "personajes_menos_usados": sorted(
                self.metricas["personajes_usados"].items(),
                key=lambda x: x[1]
            )[:10],
            "total_errores": len(self.metricas["errores"]),
            "huecos_por_categoria": self.metricas["huecos_por_categoria"]
        }

metricas_manager = MetricasManager()


# ===================================================================
# NORMALIZADOR
# ===================================================================

class Normalizador:
    SINONIMOS = {
        'hombre': 'masculino',
        'mujer': 'femenino',
        'varon': 'masculino',
        'chica': 'femenino',
        'chico': 'masculino',
        'cientifico': 'cientifico',
        'cientifica': 'cientifico',
        'artista': 'artista',
        'pintor': 'artista',
        'escritor': 'escritor',
        'escritora': 'escritor',
        'lentes': 'gafas',
        'anteojos': 'gafas',
        'existio': 'real',
        'inventado': 'ficticio',
        'poderes': 'tiene_poderes',
        'superpoderes': 'tiene_poderes',
        'dama': 'mujer',
        'celebre': 'famoso',
        'iconico': 'famoso',
        'fallecio': 'muerto',
        'murio': 'muerto',
        'fallecido': 'muerto',
        'inmortal': 'inmortal',
        'britanico': 'ingles',
        'millonario': 'rico',
        'adinerado': 'rico',
        'imaginario': 'ficticio'
    }

    @staticmethod
    def normalizar(texto: str) -> str:
        if not texto:
            return ""
        texto = texto.lower()
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
        signos = '¿?¡!.,;:()[]{}"\'-'
        for signo in signos:
            texto = texto.replace(signo, ' ')
        texto = ' '.join(texto.split())
        palabras = texto.split()
        palabras_procesadas = [Normalizador.SINONIMOS.get(p, p) for p in palabras]
        return ' '.join(palabras_procesadas)


# ===================================================================
# REGISTRO DE HUECOS
# ===================================================================

def registrar_hueco(pregunta: str, personaje: Dict, pregunta_norm: str):
    try:
        if os.path.exists(REGISTRO_HUECOS_FILE):
            with open(REGISTRO_HUECOS_FILE, 'r', encoding='utf-8') as f:
                registros = json.load(f)
        else:
            registros = []
        registros.append({
            "timestamp": datetime.now().isoformat(),
            "pregunta_original": pregunta,
            "pregunta_normalizada": pregunta_norm,
            "personaje": personaje.get("nombre", "desconocido")
        })
        if len(registros) > 1000:
            registros = registros[-1000:]
        with open(REGISTRO_HUECOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(registros, f, ensure_ascii=False, indent=2)
        metricas_manager.registrar_hueco_categoria("pregunta_no_clasificable")
        print(f"📝 Hueco registrado: '{pregunta}' para {personaje.get('nombre')}")
    except Exception as e:
        print(f"⚠️ Error registrando hueco: {e}")
        metricas_manager.registrar_error(str(e), "registrar_hueco")


# ===================================================================
# ANALIZADOR DE PREGUNTAS (VERSIÓN HÍBRIDA)
# ===================================================================

class AnalizadorPreguntas:
    @staticmethod
    def analizar(pregunta: str, personaje: Dict) -> Dict:
        pregunta_norm = Normalizador.normalizar(pregunta)

        # ---------- TIPO ----------
        if 'real' in pregunta_norm or 'existio' in pregunta_norm or 'carne y hueso' in pregunta_norm:
            es_real = personaje.get('tipo') == 'real'
            return {'answer': 'Sí' if es_real else 'No', 'clarification': ''}
        if 'ficticio' in pregunta_norm or 'inventado' in pregunta_norm or 'imaginario' in pregunta_norm:
            es_ficticio = personaje.get('tipo') == 'ficticio'
            return {'answer': 'Sí' if es_ficticio else 'No', 'clarification': ''}

        # ---------- GÉNERO ----------
        if 'masculino' in pregunta_norm or 'hombre' in pregunta_norm:
            es_hombre = personaje.get('genero') == 'masculino'
            return {'answer': 'Sí' if es_hombre else 'No', 'clarification': ''}
        if 'femenino' in pregunta_norm or 'mujer' in pregunta_norm or 'dama' in pregunta_norm:
            es_mujer = personaje.get('genero') == 'femenino'
            return {'answer': 'Sí' if es_mujer else 'No', 'clarification': ''}

        # ---------- VITAL ----------
        if 'vivo' in pregunta_norm or 'vive' in pregunta_norm:
            vivo = personaje.get('vivo', False)
            return {'answer': 'Sí' if vivo else 'No', 'clarification': ''}
        if 'muerto' in pregunta_norm or 'murio' in pregunta_norm or 'fallecido' in pregunta_norm:
            muerto = not personaje.get('vivo', True)
            return {'answer': 'Sí' if muerto else 'No', 'clarification': ''}

        # ---------- FAMA ----------
        if 'famoso' in pregunta_norm or 'conocido' in pregunta_norm or 'celebre' in pregunta_norm:
            famoso = personaje.get('famoso', False)
            return {'answer': 'Sí' if famoso else 'No', 'clarification': ''}
        if 'todo el mundo' in pregunta_norm or 'todo mundo' in pregunta_norm:
            conocido = personaje.get('famoso', False)
            return {'answer': 'Sí' if conocido else 'No', 'clarification': ''}

        # ---------- RIQUEZA ----------
        if 'rico' in pregunta_norm or 'millonario' in pregunta_norm or 'adinerado' in pregunta_norm:
            rico = personaje.get('rico', False)
            return {'answer': 'Sí' if rico else 'No', 'clarification': ''}
        if 'pobre' in pregunta_norm:
            pobre = personaje.get('pobre', False)
            return {'answer': 'Sí' if pobre else 'No', 'clarification': ''}

        # ---------- PROFESIÓN ----------
        if 'cientifico' in pregunta_norm:
            es_cientifico = personaje.get('profesion') in ['cientifico', 'cientifica'] or personaje.get('area') in ['fisica', 'quimica']
            return {'answer': 'Sí' if es_cientifico else 'No', 'clarification': ''}
        if 'artista' in pregunta_norm or 'pintor' in pregunta_norm:
            es_artista = personaje.get('profesion') == 'artista' or personaje.get('area') == 'arte'
            return {'answer': 'Sí' if es_artista else 'No', 'clarification': ''}
        if 'escritor' in pregunta_norm or 'autor' in pregunta_norm:
            es_escritor = personaje.get('profesion') == 'escritor' or personaje.get('area') == 'literatura'
            return {'answer': 'Sí' if es_escritor else 'No', 'clarification': ''}
        if 'militar' in pregunta_norm or 'soldado' in pregunta_norm or 'guerrero' in pregunta_norm:
            es_militar = personaje.get('profesion') in ['militar', 'guerrera'] or personaje.get('area') == 'guerra'
            return {'answer': 'Sí' if es_militar else 'No', 'clarification': ''}
        if 'mago' in pregunta_norm or 'bruja' in pregunta_norm:
            es_mago = personaje.get('profesion') in ['mago', 'bruja'] or personaje.get('area') == 'magia'
            return {'answer': 'Sí' if es_mago else 'No', 'clarification': ''}
        if 'superheroe' in pregunta_norm or 'heroe' in pregunta_norm:
            es_heroe = personaje.get('profesion') == 'superheroe'
            return {'answer': 'Sí' if es_heroe else 'No', 'clarification': ''}
        if 'villano' in pregunta_norm or 'malo' in pregunta_norm:
            es_villano = personaje.get('profesion') == 'villano'
            return {'answer': 'Sí' if es_villano else 'No', 'clarification': ''}
        if 'detective' in pregunta_norm:
            es_detective = personaje.get('profesion') == 'detective'
            return {'answer': 'Sí' if es_detective else 'No', 'clarification': ''}
        if 'dramaturgo' in pregunta_norm:
            es_dramaturgo = personaje.get('profesion') == 'escritor' and 'teatro' in personaje.get('area', '')
            return {'answer': 'Sí' if es_dramaturgo else 'No', 'clarification': ''}
        if 'inventor' in pregunta_norm:
            es_inventor = personaje.get('rol', {}).get('es_inventor', False)
            return {'answer': 'Sí' if es_inventor else 'No', 'clarification': ''}
        if 'presidente' in pregunta_norm:
            es_presidente = any('presidente' in str(c).lower() for c in personaje.get('caracteristicas', []))
            return {'answer': 'Sí' if es_presidente else 'No', 'clarification': ''}
        if 'escultor' in pregunta_norm:
            es_escultor = personaje.get('profesion') == 'escultor'
            return {'answer': 'Sí' if es_escultor else 'No', 'clarification': ''}

        # ---------- NACIONALIDAD ----------
        if 'europa' in pregunta_norm or 'europeo' in pregunta_norm:
            europa = personaje.get('nacionalidad') in ['aleman', 'frances', 'ingles', 'italiano', 'espanol', 'polaca', 'francesa', 'inglesa']
            return {'answer': 'Sí' if europa else 'No', 'clarification': ''}
        if 'america' in pregunta_norm or 'americano' in pregunta_norm:
            america = personaje.get('nacionalidad') in ['americano', 'estadounidense', 'mexicana']
            return {'answer': 'Sí' if america else 'No', 'clarification': ''}
        if 'asia' in pregunta_norm or 'asiatico' in pregunta_norm:
            asia = personaje.get('nacionalidad') in ['chino', 'japones', 'indio']
            return {'answer': 'Sí' if asia else 'No', 'clarification': ''}
        if 'aleman' in pregunta_norm:
            es_aleman = personaje.get('nacionalidad') == 'aleman'
            return {'answer': 'Sí' if es_aleman else 'No', 'clarification': ''}
        if 'frances' in pregunta_norm:
            es_frances = personaje.get('nacionalidad') == 'frances'
            return {'answer': 'Sí' if es_frances else 'No', 'clarification': ''}
        if 'ingles' in pregunta_norm or 'britanico' in pregunta_norm:
            es_ingles = personaje.get('nacionalidad') == 'ingles'
            return {'answer': 'Sí' if es_ingles else 'No', 'clarification': ''}
        if 'italiano' in pregunta_norm:
            es_italiano = personaje.get('nacionalidad') == 'italiano'
            return {'answer': 'Sí' if es_italiano else 'No', 'clarification': ''}
        if 'espanol' in pregunta_norm:
            es_espanol = personaje.get('nacionalidad') == 'espanol'
            return {'answer': 'Sí' if es_espanol else 'No', 'clarification': ''}
        if 'polaco' in pregunta_norm:
            es_polaco = personaje.get('nacionalidad') == 'polaca'
            return {'answer': 'Sí' if es_polaco else 'No', 'clarification': ''}
        if 'chino' in pregunta_norm:
            es_chino = personaje.get('nacionalidad') == 'china'
            return {'answer': 'Sí' if es_chino else 'No', 'clarification': ''}
        if 'mexicano' in pregunta_norm:
            es_mexicano = personaje.get('nacionalidad') == 'mexicana'
            return {'answer': 'Sí' if es_mexicano else 'No', 'clarification': ''}
        if 'estadounidense' in pregunta_norm or 'usa' in pregunta_norm:
            es_usa = personaje.get('nacionalidad') == 'americano'
            return {'answer': 'Sí' if es_usa else 'No', 'clarification': ''}

        # ---------- ÉPOCA ----------
        if 'antigua' in pregunta_norm or 'antiguedad' in pregunta_norm:
            es_antigua = personaje.get('epoca') == 'antigua' or personaje.get('periodo', {}).get('vivio_antiguedad', False)
            return {'answer': 'Sí' if es_antigua else 'No', 'clarification': ''}
        if 'medieval' in pregunta_norm or 'edad media' in pregunta_norm:
            es_medieval = personaje.get('epoca') == 'medieval' or personaje.get('periodo', {}).get('es_medieval', False)
            return {'answer': 'Sí' if es_medieval else 'No', 'clarification': ''}
        if 'renacimiento' in pregunta_norm:
            es_renacimiento = personaje.get('epoca') == 'renacimiento'
            return {'answer': 'Sí' if es_renacimiento else 'No', 'clarification': ''}
        if 'moderna' in pregunta_norm or 'moderno' in pregunta_norm:
            es_moderna = personaje.get('epoca') in ['moderna', 'contemporaneo', 'victoriana']
            return {'answer': 'Sí' if es_moderna else 'No', 'clarification': ''}
        if 'futuro' in pregunta_norm or 'futurista' in pregunta_norm:
            es_futuro = personaje.get('epoca') == 'futuro'
            return {'answer': 'Sí' if es_futuro else 'No', 'clarification': ''}

        # ---------- SIGLO ----------
        if 'siglo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            siglo_inicio = periodo.get('siglo_inicio', 0)
            siglo_fin = periodo.get('siglo_fin', 0)
            match = re.search(r'siglo\s+(\d+)', pregunta_norm)
            if match:
                siglo_preg = int(match.group(1))
                if siglo_inicio <= siglo_preg <= siglo_fin:
                    return {'answer': 'Sí', 'clarification': ''}
                else:
                    return {'answer': 'No', 'clarification': ''}
            if siglo_inicio > 0:
                return {'answer': f'Sí, siglo {siglo_inicio}' if siglo_inicio == siglo_fin else f'Siglos {siglo_inicio} al {siglo_fin}', 'clarification': ''}
        if 'antes de cristo' in pregunta_norm or 'antes cristo' in pregunta_norm:
            antes_cristo = personaje.get('periodo', {}).get('antes_de_cristo', False)
            return {'answer': 'Sí' if antes_cristo else 'No', 'clarification': ''}

        # ---------- UNIVERSO ----------
        if 'dc' in pregunta_norm:
            es_dc = personaje.get('universo') == 'DC'
            return {'answer': 'Sí' if es_dc else 'No', 'clarification': ''}
        if 'marvel' in pregunta_norm:
            es_marvel = personaje.get('universo') == 'Marvel'
            return {'answer': 'Sí' if es_marvel else 'No', 'clarification': ''}
        if 'harry potter' in pregunta_norm:
            es_hp = personaje.get('universo') == 'Harry Potter'
            return {'answer': 'Sí' if es_hp else 'No', 'clarification': ''}
        if 'star wars' in pregunta_norm:
            es_sw = personaje.get('universo') == 'Star Wars'
            return {'answer': 'Sí' if es_sw else 'No', 'clarification': ''}
        if 'senor de los anillos' in pregunta_norm:
            es_lotr = personaje.get('universo') == 'Tolkien'
            return {'answer': 'Sí' if es_lotr else 'No', 'clarification': ''}

        # ---------- CARACTERÍSTICAS FÍSICAS ----------
        if 'gafas' in pregunta_norm or 'lentes' in pregunta_norm:
            usa_gafas = 'gafas' in ' '.join(personaje.get('caracteristicas', [])).lower()
            return {'answer': 'Sí' if usa_gafas else 'No', 'clarification': ''}
        if 'barba' in pregunta_norm:
            tiene_barba = 'barba' in ' '.join(personaje.get('caracteristicas', [])).lower()
            return {'answer': 'Sí' if tiene_barba else 'No', 'clarification': ''}
        if 'calvo' in pregunta_norm:
            es_calvo = personaje.get('fisico', {}).get('es_calvo', False)
            return {'answer': 'Sí' if es_calvo else 'No', 'clarification': ''}
        if 'alto' in pregunta_norm:
            es_alto = personaje.get('fisico', {}).get('alto', False)
            return {'answer': 'Sí' if es_alto else 'No', 'clarification': ''}
        if 'bajo' in pregunta_norm:
            es_bajo = personaje.get('fisico', {}).get('bajo', False)
            return {'answer': 'Sí' if es_bajo else 'No', 'clarification': ''}

        # ---------- PODERES / HABILIDADES ----------
        if 'poderes' in pregunta_norm or 'superpoderes' in pregunta_norm:
            tiene_poderes = personaje.get('tiene_poderes', False)
            return {'answer': 'Sí' if tiene_poderes else 'No', 'clarification': ''}
        if 'volar' in pregunta_norm or 'vuela' in pregunta_norm:
            puede_volar = personaje.get('habilidades', {}).get('vuela', False) or personaje.get('puede_volar', False)
            return {'answer': 'Sí' if puede_volar else 'No', 'clarification': ''}
        if 'inmortal' in pregunta_norm or 'vivir para siempre' in pregunta_norm:
            inmortal = personaje.get('habilidades', {}).get('es_inmortal', False) or personaje.get('es_inmortal', False)
            return {'answer': 'Sí' if inmortal else 'No', 'clarification': ''}
        if 'fuerza sobrehumana' in pregunta_norm:
            fuerza = personaje.get('habilidades', {}).get('fuerza_sobrehumana', False)
            return {'answer': 'Sí' if fuerza else 'No', 'clarification': ''}
        if 'habilidades especiales' in pregunta_norm:
            especiales = personaje.get('habilidades', {}).get('tiene_habilidades_especiales', False)
            return {'answer': 'Sí' if especiales else 'No', 'clarification': ''}

        # ---------- ARMAS / OBJETOS ----------
        if 'arco' in pregunta_norm:
            tiene_arco = personaje.get('armas_objetos', {}).get('tiene_arco', False)
            return {'answer': 'Sí' if tiene_arco else 'No', 'clarification': ''}
        if 'espada' in pregunta_norm:
            tiene_espada = personaje.get('armas_objetos', {}).get('usa_espada', False)
            return {'answer': 'Sí' if tiene_espada else 'No', 'clarification': ''}
        if 'arma' in pregunta_norm and ('porta' in pregunta_norm or 'usa' in pregunta_norm):
            porta = personaje.get('armas_objetos', {}).get('porta_armas', False)
            return {'answer': 'Sí' if porta else 'No', 'clarification': ''}
        if 'gadgets' in pregunta_norm:
            tiene_gadgets = personaje.get('armas_objetos', {}).get('tiene_gadgets', False)
            return {'answer': 'Sí' if tiene_gadgets else 'No', 'clarification': ''}
        if 'tecnologia' in pregunta_norm and 'avanzada' in pregunta_norm:
            tech = personaje.get('armas_objetos', {}).get('usa_tecnologia_avanzada', False)
            return {'answer': 'Sí' if tech else 'No', 'clarification': ''}

        # ---------- LOGROS / IMPACTO ----------
        if 'premio nobel' in pregunta_norm or 'nobel' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            tiene_nobel = any('nobel' in str(p).lower() for p in impacto.get('premios', []))
            return {'answer': 'Sí' if tiene_nobel else 'No', 'clarification': ''}
        if 'premio' in pregunta_norm and 'nobel' not in pregunta_norm:
            impacto = personaje.get('impacto', {})
            tiene_premios = len(impacto.get('premios', [])) > 0
            return {'answer': 'Sí' if tiene_premios else 'No', 'clarification': ''}
        if 'revolucion' in pregunta_norm or 'revoluciono' in pregunta_norm:
            revoluciono = personaje.get('impacto', {}).get('revoluciono_campo', False)
            return {'answer': 'Sí' if revoluciono else 'No', 'clarification': ''}
        if 'cambio' in pregunta_norm and 'historia' in pregunta_norm:
            cambio = personaje.get('impacto', {}).get('cambio_historia', False)
            return {'answer': 'Sí' if cambio else 'No', 'clarification': ''}
        if 'descubrimiento' in pregunta_norm or 'hizo descubrimientos' in pregunta_norm:
            descubrio = personaje.get('impacto', {}).get('hizo_descubrimientos', False)
            return {'answer': 'Sí' if descubrio else 'No', 'clarification': ''}

        # ---------- PERFIL MORAL ----------
        if 'violento' in pregunta_norm or 'violencia' in pregunta_norm:
            violento = personaje.get('perfil_moral', {}).get('violento', False)
            return {'answer': 'Sí' if violento else 'No', 'clarification': ''}
        if 'pacifista' in pregunta_norm or 'paz' in pregunta_norm:
            pacifista = personaje.get('perfil_moral', {}).get('pacifista', False)
            return {'answer': 'Sí' if pacifista else 'No', 'clarification': ''}
        if 'conquistador' in pregunta_norm or 'conquisto' in pregunta_norm:
            conquistador = personaje.get('perfil_moral', {}).get('conquistador', False)
            return {'answer': 'Sí' if conquistador else 'No', 'clarification': ''}
        if 'imperialista' in pregunta_norm or 'imperio' in pregunta_norm:
            imperialista = personaje.get('perfil_moral', {}).get('imperialista', False)
            return {'answer': 'Sí' if imperialista else 'No', 'clarification': ''}
        if 'lucho' in pregunta_norm and 'libertad' in pregunta_norm:
            lucho = personaje.get('perfil_moral', {}).get('lucho_libertad', False)
            return {'answer': 'Sí' if lucho else 'No', 'clarification': ''}

        # ---------- ROL ----------
        if 'lider' in pregunta_norm:
            lider = personaje.get('rol', {}).get('lider', False)
            return {'answer': 'Sí' if lider else 'No', 'clarification': ''}
        if 'gobernante' in pregunta_norm or 'goberno' in pregunta_norm:
            gobernante = personaje.get('rol', {}).get('gobernante', False)
            return {'answer': 'Sí' if gobernante else 'No', 'clarification': ''}
        if 'general' in pregunta_norm:
            general = personaje.get('rol', {}).get('general', False)
            return {'answer': 'Sí' if general else 'No', 'clarification': ''}
        if 'antagonista' in pregunta_norm:
            antagonista = personaje.get('rol', {}).get('antagonista', False)
            return {'answer': 'Sí' if antagonista else 'No', 'clarification': ''}

        # ---------- IDEOLOGÍA ----------
        if 'liberal' in pregunta_norm:
            liberal = personaje.get('ideologia', {}).get('liberal', False)
            return {'answer': 'Sí' if liberal else 'No', 'clarification': ''}
        if 'conservador' in pregunta_norm:
            conservador = personaje.get('ideologia', {}).get('conservador', False)
            return {'answer': 'Sí' if conservador else 'No', 'clarification': ''}

        # ---------- ICÓNICO ----------
        if 'iconico' in pregunta_norm or 'figura iconica' in pregunta_norm:
            iconico = personaje.get('impacto', {}).get('iconico', False)
            return {'answer': 'Sí' if iconico else 'No', 'clarification': ''}

        # ---------- NO CLASIFICABLE ----------
        registrar_hueco(pregunta, personaje, pregunta_norm)
        return {'answer': 'No lo sé', 'clarification': 'No estoy seguro de cómo interpretar eso. ¿Podrías reformularlo?'}


# ===================================================================
# GENERADOR DE SUGERENCIAS
# ===================================================================

class GeneradorSugerencias:
    SUGERENCIAS_BASE = [
        "¿Es una persona real?",
        "¿Es hombre?",
        "¿Es mujer?",
        "¿Está vivo actualmente?",
        "¿Es famoso?",
        "¿Es rico?",
        "¿Tiene poderes?",
        "¿Es científico?",
        "¿Es artista?",
        "¿Es escritor?",
        "¿Es militar?",
        "¿Es un superhéroe?",
        "¿Es de Europa?",
        "¿Es de América?",
        "¿Es de época antigua?",
        "¿Es de época moderna?",
        "¿Pertenece a DC Comics?",
        "¿Pertenece a Marvel?",
        "¿Usa gafas?",
        "¿Tiene barba?",
        "¿Es mago?",
        "¿Es detective?",
        "¿Es un ser imaginario?",
        "¿Falleció?",
        "¿Es una figura icónica?",
        "¿Tiene un arco?",
        "¿Es inmortal?",
        "¿Es pacifista?",
        "¿Es violento?",
        "¿Es bajo?",
        "¿Es alto?",
        "¿Es calvo?",
        "¿Es de Asia?",
        "¿Es de África?",
        "¿Es del futuro?",
        "¿Es del Señor de los Anillos?",
        "¿Es de Star Wars?",
        "¿Es de Harry Potter?"
    ]

    @staticmethod
    def generar(preguntas_hechas: List[str], max_sugerencias: int = 5) -> List[str]:
        preguntas_norm = [Normalizador.normalizar(p) for p in preguntas_hechas]
        disponibles = []
        for sug in GeneradorSugerencias.SUGERENCIAS_BASE:
            sug_norm = Normalizador.normalizar(sug)
            ya_preguntada = False
            for p_norm in preguntas_norm:
                palabras_sug = set(sug_norm.split())
                palabras_preg = set(p_norm.split())
                if len(palabras_sug & palabras_preg) >= 2:
                    ya_preguntada = True
                    break
            if not ya_preguntada:
                disponibles.append(sug)
            if len(disponibles) >= max_sugerencias * 2:
                break
        return disponibles[:max_sugerencias]


# ===================================================================
# MEMORIA DE PARTIDA
# ===================================================================

class MemoriaPartida:
    def __init__(self, personaje_nombre: str):
        self.personaje_nombre = personaje_nombre
        self.preguntas = []
        self.respuestas = []
        self.preguntas_restantes = MAX_PREGUNTAS
        self.inicio = datetime.now()

    def registrar(self, pregunta: str, respuesta: str):
        self.preguntas.append(pregunta)
        self.respuestas.append(respuesta)
        self.preguntas_restantes -= 1
        metricas_manager.registrar_pregunta(pregunta)

    def puede_seguir(self) -> bool:
        return self.preguntas_restantes > 0

    def finalizar(self, ganado: bool):
        metricas_manager.registrar_resultado(self.personaje_nombre, ganado)

memorias = {}


# ===================================================================
# ENDPOINTS DEL JUEGO
# ===================================================================

analizador = AnalizadorPreguntas()
generador = GeneradorSugerencias()

@app.route('/api/oracle', methods=['POST'])
def oracle():
    try:
        data = request.get_json()
        action = data.get('action')
        session_id = data.get('session_id', 'default')

        if action == 'start':
            character = random.choice(PERSONAJES)
            memorias[session_id] = MemoriaPartida(character['nombre'])
            metricas_manager.registrar_partida_iniciada(character['nombre'])
            return jsonify({
                'character': character,
                'message': 'Juego iniciado',
                'session_id': session_id
            })

        elif action == 'ask':
            question = data.get('question', '').strip()
            character = data.get('character', {})
            if not question:
                return jsonify({'answer': 'No lo sé', 'clarification': ''})

            if session_id not in memorias:
                memorias[session_id] = MemoriaPartida(character.get('nombre', 'desconocido'))
            memoria = memorias[session_id]

            if not memoria.puede_seguir():
                memoria.finalizar(False)
                return jsonify({'answer': 'Has agotado tus preguntas. Debes adivinar.', 'clarification': ''})

            respuesta = analizador.analizar(question, character)
            if respuesta['answer'] == 'No lo sé':
                registrar_hueco(question, character, Normalizador.normalizar(question))
            memoria.registrar(question, respuesta['answer'])
            return jsonify(respuesta)

        elif action == 'guess':
            guess = data.get('guess', '').lower().strip()
            character = data.get('character', {})
            character_name = character.get('nombre', '').lower().strip()
            guess_norm = Normalizador.normalizar(guess)
            name_norm = Normalizador.normalizar(character_name)
            correct = guess_norm == name_norm
            if session_id in memorias:
                memorias[session_id].finalizar(correct)
            return jsonify({'correct': correct, 'character': character['nombre']})

        elif action == 'suggestions':
            if session_id in memorias:
                preguntas_hechas = memorias[session_id].preguntas
            else:
                preguntas_hechas = []
            suggestions = generador.generar(preguntas_hechas, 5)
            return jsonify({'suggestions': suggestions})

        elif action == 'hint':
            character = data.get('character', {})
            hint_level = data.get('hint_level', 1)
            pistas = character.get('pistas', [])
            if hint_level == 1 and len(pistas) > 0:
                hint = pistas[0]
            elif hint_level == 2 and len(pistas) > 1:
                hint = pistas[1]
            else:
                hint = "No hay más pistas disponibles."
            return jsonify({'hint': hint})

        else:
            return jsonify({'error': 'Acción no válida'}), 400

    except Exception as e:
        print(f"❌ Error: {e}")
        metricas_manager.registrar_error(str(e), f"oracle_endpoint_{action}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ===================================================================
# ENDPOINTS DEL DASHBOARD
# ===================================================================

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    try:
        stats = metricas_manager.obtener_estadisticas()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/huecos', methods=['GET'])
def dashboard_huecos():
    try:
        limit = request.args.get('limit', 50, type=int)
        if os.path.exists(REGISTRO_HUECOS_FILE):
            with open(REGISTRO_HUECOS_FILE, 'r', encoding='utf-8') as f:
                huecos = json.load(f)
            preguntas_counter = Counter([h['pregunta_normalizada'] for h in huecos])
            personajes_counter = Counter([h['personaje'] for h in huecos])
            return jsonify({
                'total': len(huecos),
                'ultimos': huecos[-limit:],
                'preguntas_frecuentes': preguntas_counter.most_common(20),
                'personajes_problematicos': personajes_counter.most_common(10)
            })
        else:
            return jsonify({'total': 0, 'ultimos': [], 'preguntas_frecuentes': [], 'personajes_problematicos': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/personajes', methods=['GET'])
def dashboard_personajes():
    try:
        personajes_stats = []
        for p in PERSONAJES:
            nombre = p['nombre']
            veces_usado = metricas_manager.metricas['personajes_usados'].get(nombre, 0)
            tasa_exito = metricas_manager.metricas['tasa_exito_por_personaje'].get(nombre, {"ganadas": 0, "perdidas": 0})
            total_partidas = tasa_exito['ganadas'] + tasa_exito['perdidas']
            porcentaje = round(tasa_exito['ganadas'] / total_partidas * 100, 2) if total_partidas > 0 else 0
            personajes_stats.append({
                'nombre': nombre,
                'tipo': p.get('tipo', ''),
                'veces_usado': veces_usado,
                'partidas_ganadas': tasa_exito['ganadas'],
                'partidas_perdidas': tasa_exito['perdidas'],
                'porcentaje_victoria': porcentaje
            })
        personajes_stats.sort(key=lambda x: x['veces_usado'], reverse=True)
        return jsonify({'personajes': personajes_stats, 'total_personajes': len(PERSONAJES)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/errores', methods=['GET'])
def dashboard_errores():
    try:
        limit = request.args.get('limit', 50, type=int)
        errores = metricas_manager.metricas.get('errores', [])
        return jsonify({'total': len(errores), 'ultimos': errores[-limit:]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/exportar-txt', methods=['GET'])
def exportar_txt():
    try:
        with open(METRICAS_FILE, 'r', encoding='utf-8') as f:
            metricas = json.load(f)
    except:
        metricas = {}
    try:
        with open(REGISTRO_HUECOS_FILE, 'r', encoding='utf-8') as f:
            huecos = json.load(f)
    except:
        huecos = []

    output = StringIO()
    output.write("=" * 80 + "\n")
    output.write("THE ORACLE - REPORTE DE DASHBOARD\n")
    output.write("=" * 80 + "\n")
    output.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.write("=" * 80 + "\n\n")

    output.write("ESTADÍSTICAS GENERALES\n")
    output.write("-" * 80 + "\n")
    output.write(f"Partidas Totales: {metricas.get('partidas_totales', 0)}\n")
    output.write(f"Partidas Ganadas: {metricas.get('partidas_ganadas', 0)}\n")
    output.write(f"Partidas Perdidas: {metricas.get('partidas_perdidas', 0)}\n")
    total = metricas.get('partidas_totales', 0)
    ganadas = metricas.get('partidas_ganadas', 0)
    tasa = (ganadas / total * 100) if total > 0 else 0
    output.write(f"Tasa de Victoria: {tasa:.2f}%\n")
    output.write(f"Preguntas Totales: {metricas.get('preguntas_totales', 0)}\n")
    promedio = (metricas.get('preguntas_totales', 0) / total) if total > 0 else 0
    output.write(f"Promedio Preguntas/Partida: {promedio:.2f}\n\n")

    output.write("PERSONAJES MÁS JUGADOS (Top 20)\n")
    output.write("-" * 80 + "\n")
    personajes_usados = metricas.get('personajes_usados', {})
    personajes_sorted = sorted(personajes_usados.items(), key=lambda x: x[1], reverse=True)
    for i, (nombre, veces) in enumerate(personajes_sorted[:20], 1):
        output.write(f"{i:2d}. {nombre:30s} - {veces:3d} veces\n")
    output.write("\n")

    output.write("ANÁLISIS DE HUECOS\n")
    output.write("-" * 80 + "\n")
    output.write(f"Total de Huecos: {len(huecos)}\n\n")
    from collections import Counter
    preguntas_counter = Counter([h['pregunta_normalizada'] for h in huecos])
    output.write("Top 30 Preguntas Más Frecuentes (Sin Respuesta):\n")
    output.write("-" * 80 + "\n")
    for i, (pregunta, cantidad) in enumerate(preguntas_counter.most_common(30), 1):
        output.write(f"{i:2d}. [{cantidad:3d}x] {pregunta}\n")
    output.write("\n")
    personajes_counter = Counter([h['personaje'] for h in huecos])
    output.write("Top 15 Personajes con Más Huecos:\n")
    output.write("-" * 80 + "\n")
    for i, (personaje, cantidad) in enumerate(personajes_counter.most_common(15), 1):
        output.write(f"{i:2d}. {personaje:30s} - {cantidad:3d} huecos\n")
    output.write("\n")

    output.write("ÚLTIMOS 50 HUECOS REGISTRADOS\n")
    output.write("-" * 80 + "\n")
    output.write(f"{'Fecha/Hora':<20} {'Personaje':<25} {'Pregunta':<35}\n")
    output.write("-" * 80 + "\n")
    for hueco in reversed(huecos[-50:]):
        timestamp = hueco.get('timestamp', '')[:19]
        personaje = hueco.get('personaje', '')[:24]
        pregunta = hueco.get('pregunta_original', '')[:34]
        output.write(f"{timestamp:<20} {personaje:<25} {pregunta:<35}\n")
    output.write("\n")
    output.write("=" * 80 + "\n")
    output.write("FIN DEL REPORTE\n")
    output.write("=" * 80 + "\n")

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=oracle_dashboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    return response


# ===================================================================
# DASHBOARD HTML
# ===================================================================

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠 Oracle Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            border: 2px solid #ff00ff;
        }
        h1 {
            color: #ff00ff;
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 0 0 20px #ff00ff;
        }
        .subtitle {
            color: #00ff00;
            font-size: 1.2em;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .tab-button {
            padding: 15px 30px;
            background: rgba(255, 0, 255, 0.2);
            border: 2px solid #ff00ff;
            color: #ff00ff;
            cursor: pointer;
            border-radius: 10px;
            font-size: 1em;
            transition: all 0.3s;
        }
        .tab-button:hover {
            background: rgba(255, 0, 255, 0.4);
            transform: translateY(-2px);
        }
        .tab-button.active {
            background: #ff00ff;
            color: #1a1a2e;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(0, 0, 0, 0.4);
            padding: 25px;
            border-radius: 15px;
            border: 2px solid #00ff00;
            text-align: center;
        }
        .stat-value {
            font-size: 3em;
            color: #00ff00;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            color: #e0e0e0;
            font-size: 1em;
        }
        .section {
            background: rgba(0, 0, 0, 0.4);
            padding: 25px;
            border-radius: 15px;
            border: 2px solid #00ff00;
            margin-bottom: 30px;
        }
        .section h2 {
            color: #00ff00;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th {
            background: rgba(0, 255, 0, 0.2);
            padding: 15px;
            text-align: left;
            color: #00ff00;
            border-bottom: 2px solid #00ff00;
        }
        td {
            padding: 12px 15px;
            border-bottom: 1px solid rgba(0, 255, 0, 0.2);
        }
        tr:hover {
            background: rgba(0, 255, 0, 0.1);
        }
        .badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin-right: 10px;
        }
        .badge-success {
            background: rgba(0, 255, 0, 0.3);
            color: #00ff00;
        }
        .badge-error {
            background: rgba(255, 0, 0, 0.3);
            color: #ff0000;
        }
        .badge-warning {
            background: rgba(255, 165, 0, 0.3);
            color: #ffA500;
        }
        .refresh-button {
            padding: 12px 25px;
            background: #00ff00;
            color: #000;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s;
        }
        .refresh-button:hover {
            background: #ff00ff;
            transform: scale(1.05);
        }
        .loading {
            text-align: center;
            padding: 50px;
            font-size: 1.5em;
            color: #00ff00;
        }
        .empty-state {
            text-align: center;
            padding: 50px;
            color: #666;
            font-size: 1.2em;
        }
        @media (max-width: 768px) {
            h1 { font-size: 2em; }
            .stats-grid { grid-template-columns: 1fr; }
            .tabs { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧠 THE ORACLE</h1>
            <p class="subtitle">Panel de Control y Métricas</p>
            <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                <button class="refresh-button" onclick="loadAllData()">🔄 Actualizar Datos</button>
                <button class="refresh-button" onclick="exportarTXT()" style="background: #00ff00;">📄 Descargar TXT</button>
            </div>
        </header>

        <div class="tabs">
            <button class="tab-button active" onclick="switchTab('general')">📊 General</button>
            <button class="tab-button" onclick="switchTab('personajes')">🎭 Personajes</button>
            <button class="tab-button" onclick="switchTab('huecos')">🕳️ Huecos</button>
            <button class="tab-button" onclick="switchTab('errores')">⚠️ Errores</button>
        </div>

        <div id="tab-general" class="tab-content active">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Partidas Totales</div>
                    <div class="stat-value" id="stat-partidas">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Partidas Ganadas</div>
                    <div class="stat-value" id="stat-ganadas">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Tasa de Victoria</div>
                    <div class="stat-value" id="stat-tasa">-%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Preguntas Totales</div>
                    <div class="stat-value" id="stat-preguntas">-</div>
                </div>
            </div>
            <div class="section">
                <h2>🎯 Personajes Más Jugados</h2>
                <table id="table-mas-usados">
                    <thead><tr><th>#</th><th>Personaje</th><th>Veces Usado</th></tr></thead>
                    <tbody><tr><td colspan="3" class="loading">Cargando...</td></tr></tbody>
                </table>
            </div>
            <div class="section">
                <h2>🎲 Personajes Menos Jugados</h2>
                <table id="table-menos-usados">
                    <thead><tr><th>#</th><th>Personaje</th><th>Veces Usado</th></tr></thead>
                    <tbody><tr><td colspan="3" class="loading">Cargando...</td></tr></tbody>
                </table>
            </div>
        </div>

        <div id="tab-personajes" class="tab-content">
            <div class="section">
                <h2>🎭 Estadísticas por Personaje</h2>
                <table id="table-personajes">
                    <thead><tr><th>Personaje</th><th>Tipo</th><th>Veces Usado</th><th>Ganadas</th><th>Perdidas</th><th>% Victoria</th><th>Dificultad</th></tr></thead>
                    <tbody><tr><td colspan="7" class="loading">Cargando...</td></tr></tbody>
                </table>
            </div>
        </div>

        <div id="tab-huecos" class="tab-content">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total de Huecos</div>
                    <div class="stat-value" id="stat-huecos-total">-</div>
                </div>
            </div>
            <div class="section">
                <h2>❓ Preguntas Más Frecuentes (No Respondidas)</h2>
                <table id="table-huecos-frecuentes">
                    <thead><tr><th>#</th><th>Pregunta</th><th>Ocurrencias</th></tr></thead>
                    <tbody><tr><td colspan="3" class="loading">Cargando...</td></tr></tbody>
                </table>
            </div>
            <div class="section">
                <h2>🎭 Personajes con Más Huecos</h2>
                <table id="table-personajes-problematicos">
                    <thead><tr><th>#</th><th>Personaje</th><th>Huecos</th></tr></thead>
                    <tbody><tr><td colspan="3" class="loading">Cargando...</td></tr></tbody>
                </table>
            </div>
            <div class="section">
                <h2>📝 Últimos Huecos Registrados</h2>
                <table id="table-huecos-recientes">
                    <thead><tr><th>Fecha</th><th>Pregunta</th><th>Personaje</th></tr></thead>
                    <tbody><tr><td colspan="3" class="loading">Cargando...</td></tr></tbody>
                </table>
            </div>
        </div>

        <div id="tab-errores" class="tab-content">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total de Errores</div>
                    <div class="stat-value" id="stat-errores-total">-</div>
                </div>
            </div>
            <div class="section">
                <h2>⚠️ Errores del Sistema</h2>
                <table id="table-errores">
                    <thead><tr><th>Fecha</th><th>Error</th><th>Contexto</th></tr></thead>
                    <tbody><tr><td colspan="3" class="loading">Cargando...</td></tr></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.getElementById('tab-' + tabName).classList.add('active');
            event.target.classList.add('active');
        }

        async function loadGeneralStats() {
            try {
                const res = await fetch('/api/dashboard/stats');
                const data = await res.json();
                document.getElementById('stat-partidas').textContent = data.partidas_totales;
                document.getElementById('stat-ganadas').textContent = data.partidas_ganadas;
                document.getElementById('stat-tasa').textContent = data.tasa_victoria + '%';
                document.getElementById('stat-preguntas').textContent = data.preguntas_totales;

                const tbody1 = document.querySelector('#table-mas-usados tbody');
                tbody1.innerHTML = (data.personajes_mas_usados || []).map((p, i) => `<tr><td>${i+1}</td><td>${p[0]}</td><td>${p[1]}</td></tr>`).join('') || '<tr><td colspan="3">No hay datos</td></tr>';
                const tbody2 = document.querySelector('#table-menos-usados tbody');
                tbody2.innerHTML = (data.personajes_menos_usados || []).map((p, i) => `<tr><td>${i+1}</td><td>${p[0]}</td><td>${p[1]}</td></tr>`).join('') || '<tr><td colspan="3">No hay datos</td></tr>';
            } catch (e) { console.error(e); }
        }

        async function loadPersonajes() {
            try {
                const res = await fetch('/api/dashboard/personajes');
                const data = await res.json();
                const tbody = document.querySelector('#table-personajes tbody');
                tbody.innerHTML = (data.personajes || []).map(p => {
                    let dificultad = 'Normal';
                    if (p.porcentaje_victoria > 70) dificultad = 'Fácil';
                    else if (p.porcentaje_victoria < 30) dificultad = 'Difícil';
                    return `<tr>
                        <td>${p.nombre}</td>
                        <td><span class="badge ${p.tipo === 'real' ? 'badge-success' : 'badge-warning'}">${p.tipo}</span></td>
                        <td>${p.veces_usado}</td>
                        <td>${p.partidas_ganadas}</td>
                        <td>${p.partidas_perdidas}</td>
                        <td>${p.porcentaje_victoria}%</td>
                        <td>${dificultad}</td>
                    </tr>`;
                }).join('') || '<tr><td colspan="7">No hay datos</td></tr>';
            } catch (e) { console.error(e); }
        }

        async function loadHuecos() {
            try {
                const res = await fetch('/api/dashboard/huecos');
                const data = await res.json();
                document.getElementById('stat-huecos-total').textContent = data.total || 0;

                const tbody1 = document.querySelector('#table-huecos-frecuentes tbody');
                tbody1.innerHTML = (data.preguntas_frecuentes || []).map((p, i) => `<tr><td>${i+1}</td><td>${p[0]}</td><td><span class="badge badge-error">${p[1]}</span></td></tr>`).join('') || '<tr><td colspan="3">No hay datos</td></tr>';

                const tbody2 = document.querySelector('#table-personajes-problematicos tbody');
                tbody2.innerHTML = (data.personajes_problematicos || []).map((p, i) => `<tr><td>${i+1}</td><td>${p[0]}</td><td><span class="badge badge-warning">${p[1]}</span></td></tr>`).join('') || '<tr><td colspan="3">No hay datos</td></tr>';

                const tbody3 = document.querySelector('#table-huecos-recientes tbody');
                tbody3.innerHTML = (data.ultimos || []).reverse().slice(0, 30).map(h => `<tr><td>${new Date(h.timestamp).toLocaleString()}</td><td>${h.pregunta_original}</td><td>${h.personaje}</td></tr>`).join('') || '<tr><td colspan="3">No hay datos</td></tr>';
            } catch (e) { console.error(e); }
        }

        async function loadErrores() {
            try {
                const res = await fetch('/api/dashboard/errores');
                const data = await res.json();
                document.getElementById('stat-errores-total').textContent = data.total || 0;
                const tbody = document.querySelector('#table-errores tbody');
                tbody.innerHTML = (data.ultimos || []).reverse().map(e => `<tr><td>${new Date(e.timestamp).toLocaleString()}</td><td><span class="badge badge-error">${e.error}</span></td><td>${e.contexto}</td></tr>`).join('') || '<tr><td colspan="3">No hay errores</td></tr>';
            } catch (e) { console.error(e); }
        }

        async function loadAllData() {
            await Promise.all([loadGeneralStats(), loadPersonajes(), loadHuecos(), loadErrores()]);
        }

        function exportarTXT() {
            window.location.href = '/api/dashboard/exportar-txt';
        }

        loadAllData();
        setInterval(loadAllData, 30000);
    </script>
</body>
</html>
'''

@app.route('/dashboard')
def dashboard():
    return render_template_string(DASHBOARD_HTML)


# ===================================================================
# ENDPOINTS BÁSICOS
# ===================================================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'personajes': len(PERSONAJES),
        'mensaje': '🧠 The Oracle - Con Dashboard de Métricas'
    })

@app.route('/')
def home():
    return """
    <html>
    <head><title>The Oracle</title></head>
    <body style="font-family:sans-serif; background:#000; color:#0f0; padding:20px; text-align:center;">
        <h1 style="color:#ff00ff;">🧠 THE ORACLE</h1>
        <p>{len(PERSONAJES)} Personajes | Sistema HÍBRIDO</p>
        <p>✅ Respuestas CORRECTAS</p>
        <p>✅ Sugerencias ÚTILES</p>
        <p>✅ Panel de Control Activo</p>
        <br>
        <a href="/dashboard" style="color:#00ff00; font-size:1.5em;">📊 Ver Dashboard</a>
    </body>
    </html>
    """


# ===================================================================
# MAIN
# ===================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🧠 THE ORACLE - Backend HÍBRIDO")
    print("=" * 60)
    print(f"📡 Servidor: http://0.0.0.0:5000")
    print(f"🎭 Personajes: {len(PERSONAJES)}")
    print(f"📊 Dashboard: http://0.0.0.0:5000/dashboard")
    print("✅ Sistema de métricas ACTIVADO")
    print("✅ Analizador con 60+ patrones")
    print("=" * 60)
    # Puerto para producción
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
