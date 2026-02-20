#!/usr/bin/env python3
"""
THE ORACLE - Backend con Panel de Control
Versión: 20 personajes + Dashboard de Métricas
- ✅ Sistema de métricas completo
- ✅ Panel de control web (/dashboard)
- ✅ Estadísticas en tiempo real
- ✅ Análisis de huecos y patrones
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import random
import unicodedata
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
from flask import send_file, make_response
from io import BytesIO, StringIO


app = Flask(__name__)
CORS(app)

# ===================================================================
# CONFIGURACIÓN
# ===================================================================

REGISTRO_HUECOS_FILE = "huecos_diccionario.json"
METRICAS_FILE = "metricas_oracle.json"
MAX_PREGUNTAS = 20

# ===================================================================
# CARGADOR DE PERSONAJES DESDE JSON
# ===================================================================
def cargar_personajes(archivo: str = 'personajes.json') -> List[Dict]:
    """
    Carga personajes desde archivo JSON externo.
    Busca en el MISMO directorio donde está este archivo.
    """
    try:
        # Obtener el directorio donde está ESTE archivo (api/)
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_completa = os.path.join(directorio_actual, archivo)
        
        print(f"🔍 Buscando personajes en: {ruta_completa}")
        
        if os.path.exists(ruta_completa):
            with open(ruta_completa, 'r', encoding='utf-8') as f:
                data = json.load(f)
                personajes = data.get('personajes', [])
                print(f"✅ {len(personajes)} personajes cargados desde {ruta_completa}")
                return personajes
        else:
            print(f"⚠️  Archivo {ruta_completa} no encontrado")
            print(f"📁 Directorio actual de trabajo: {os.getcwd()}")
            print(f"📁 Contenido del directorio api/: {os.listdir(directorio_actual)}")
            return []
    except Exception as e:
        print(f"❌ Error cargando personajes: {e}")
        return []
# 
 ===================================================================
# SISTEMA DE MÉTRICAS
# ===================================================================

class MetricasManager:
    """Gestor de métricas del juego"""
    
    def __init__(self):
        self.metricas = self.cargar_metricas()
    
    def cargar_metricas(self) -> Dict:
        """Carga métricas desde archivo"""
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
        """Guarda métricas a archivo"""
        try:
            with open(METRICAS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.metricas, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error guardando métricas: {e}")
    
    def registrar_partida_iniciada(self, personaje: str):
        """Registra inicio de partida"""
        self.metricas["partidas_totales"] += 1
        
        # Contador de personajes
        if personaje not in self.metricas["personajes_usados"]:
            self.metricas["personajes_usados"][personaje] = 0
        self.metricas["personajes_usados"][personaje] += 1
        
        self.guardar_metricas()
    
    def registrar_pregunta(self, pregunta: str):
        """Registra una pregunta hecha"""
        self.metricas["preguntas_totales"] += 1
        
        # Normalizar pregunta para contar frecuencia
        pregunta_key = pregunta.lower()[:100]  # Limitar longitud
        if pregunta_key not in self.metricas["preguntas_frecuentes"]:
            self.metricas["preguntas_frecuentes"][pregunta_key] = 0
        self.metricas["preguntas_frecuentes"][pregunta_key] += 1
        
        self.guardar_metricas()
    
    def registrar_resultado(self, personaje: str, ganado: bool):
        """Registra resultado de partida"""
        if ganado:
            self.metricas["partidas_ganadas"] += 1
        else:
            self.metricas["partidas_perdidas"] += 1
        
        # Tasa de éxito por personaje
        if personaje not in self.metricas["tasa_exito_por_personaje"]:
            self.metricas["tasa_exito_por_personaje"][personaje] = {"ganadas": 0, "perdidas": 0}
        
        if ganado:
            self.metricas["tasa_exito_por_personaje"][personaje]["ganadas"] += 1
        else:
            self.metricas["tasa_exito_por_personaje"][personaje]["perdidas"] += 1
        
        self.guardar_metricas()
    
    def registrar_hueco_categoria(self, categoria: str):
        """Registra categoría de hueco"""
        if categoria not in self.metricas["huecos_por_categoria"]:
            self.metricas["huecos_por_categoria"][categoria] = 0
        self.metricas["huecos_por_categoria"][categoria] += 1
        
        self.guardar_metricas()
    
    def registrar_error(self, error: str, contexto: str = ""):
        """Registra un error del sistema"""
        self.metricas["errores"].append({
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "contexto": contexto
        })
        
        # Mantener solo últimos 100 errores
        if len(self.metricas["errores"]) > 100:
            self.metricas["errores"] = self.metricas["errores"][-100:]
        
        self.guardar_metricas()
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene resumen de estadísticas"""
        total_partidas = self.metricas["partidas_totales"]
        ganadas = self.metricas["partidas_ganadas"]
        
        return {
            "partidas_totales": total_partidas,
            "partidas_ganadas": ganadas,
            "partidas_perdidas": self.metricas["partidas_perdidas"],
            "tasa_victoria": round(ganadas / total_partidas * 100, 2) if total_partidas > 0 else 0,
            "preguntas_totales": self.metricas["preguntas_totales"],
            "promedio_preguntas": round(self.metricas["preguntas_totales"] / total_partidas, 2) if total_partidas > 0 else 0,
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
# BASE DE DATOS - 20 PERSONAJES
# ===================================================================

# Cargar personajes desde archivo JSON
PERSONAJES = cargar_personajes()

# Validación: Verificar que se cargaron personajes
if not PERSONAJES:
    print("=" * 60)
    print("⚠️  ADVERTENCIA: No se cargaron personajes")
    print("Asegúrate de que personajes.json existe en el mismo directorio")
    print("=" * 60)


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
# SISTEMA DE RESPUESTAS MEJORADO
# ===================================================================

class AnalizadorPreguntas:
    """Sistema SIMPLIFICADO y FUNCIONAL para analizar preguntas"""
    
    @staticmethod
    def analizar(pregunta: str, personaje: Dict) -> Dict:
        pregunta_norm = Normalizador.normalizar(pregunta)
        
        # TIPO (real/ficticio)
        if 'real' in pregunta_norm or 'existio' in pregunta_norm:
            es_real = personaje.get('tipo') == 'real'
            return {'answer': 'Sí' if es_real else 'No', 'clarification': ''}
        
        if 'ficticio' in pregunta_norm or 'inventado' in pregunta_norm:
            es_ficticio = personaje.get('tipo') == 'ficticio'
            return {'answer': 'Sí' if es_ficticio else 'No', 'clarification': ''}
        
        # GÉNERO
        if 'masculino' in pregunta_norm:
            es_masculino = personaje.get('genero') == 'masculino'
            return {'answer': 'Sí' if es_masculino else 'No', 'clarification': ''}
        
        if 'femenino' in pregunta_norm:
            es_femenino = personaje.get('genero') == 'femenino'
            return {'answer': 'Sí' if es_femenino else 'No', 'clarification': ''}
        
        # VIVO/MUERTO
        if 'vivo' in pregunta_norm or 'vive' in pregunta_norm:
            vivo = personaje.get('vivo', False)
            return {'answer': 'Sí' if vivo else 'No', 'clarification': ''}
        
        if 'muerto' in pregunta_norm or 'murio' in pregunta_norm:
            muerto = not personaje.get('vivo', True)
            return {'answer': 'Sí' if muerto else 'No', 'clarification': ''}
        
        # FAMA
        if 'famoso' in pregunta_norm or 'conocido' in pregunta_norm:
            famoso = personaje.get('famoso', False)
            return {'answer': 'Sí' if famoso else 'No', 'clarification': ''}
        
        # RIQUEZA
        if 'rico' in pregunta_norm or 'millonario' in pregunta_norm:
            rico = personaje.get('rico', False)
            return {'answer': 'Sí' if rico else 'No', 'clarification': ''}
        
        # PODERES
        if 'tiene_poderes' in pregunta_norm or 'superpoderes' in pregunta_norm:
            tiene_poderes = personaje.get('tiene_poderes', False)
            return {'answer': 'Sí' if tiene_poderes else 'No', 'clarification': ''}
        
        # PROFESIONES
        if 'cientifico' in pregunta_norm or 'ciencia' in pregunta_norm:
            es_cientifico = personaje.get('profesion') in ['cientifico', 'cientifica'] or personaje.get('area') in ['fisica', 'quimica']
            return {'answer': 'Sí' if es_cientifico else 'No', 'clarification': ''}
        
        if 'artista' in pregunta_norm or 'pintor' in pregunta_norm or 'arte' in pregunta_norm:
            es_artista = personaje.get('profesion') == 'artista' or personaje.get('area') == 'arte'
            return {'answer': 'Sí' if es_artista else 'No', 'clarification': ''}
        
        if 'escritor' in pregunta_norm or 'literatura' in pregunta_norm:
            es_escritor = personaje.get('profesion') == 'escritor' or personaje.get('area') == 'literatura'
            return {'answer': 'Sí' if es_escritor else 'No', 'clarification': ''}
        
        if 'militar' in pregunta_norm or 'soldado' in pregunta_norm or 'guerrero' in pregunta_norm:
            es_militar = personaje.get('profesion') in ['militar', 'guerrera'] or personaje.get('area') == 'guerra'
            return {'answer': 'Sí' if es_militar else 'No', 'clarification': ''}
        
        if 'mago' in pregunta_norm or 'bruja' in pregunta_norm or 'magia' in pregunta_norm:
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
        
        # ÉPOCA
        if 'antigua' in pregunta_norm or 'antiguo' in pregunta_norm:
            es_antigua = personaje.get('epoca') == 'antigua'
            return {'answer': 'Sí' if es_antigua else 'No', 'clarification': ''}
        
        if 'medieval' in pregunta_norm or 'edad media' in pregunta_norm:
            es_medieval = personaje.get('epoca') == 'medieval'
            return {'answer': 'Sí' if es_medieval else 'No', 'clarification': ''}
        
        if 'moderna' in pregunta_norm or 'moderno' in pregunta_norm or 'contemporaneo' in pregunta_norm:
            es_moderna = personaje.get('epoca') in ['moderna', 'victoriana']
            return {'answer': 'Sí' if es_moderna else 'No', 'clarification': ''}
        
        # NACIONALIDAD
        if 'europa' in pregunta_norm or 'europeo' in pregunta_norm:
            es_europeo = personaje.get('nacionalidad') in ['aleman', 'frances', 'ingles', 'italiano', 'espanol', 'polaca', 'francesa', 'inglesa']
            return {'answer': 'Sí' if es_europeo else 'No', 'clarification': ''}
        
        if 'america' in pregunta_norm or 'americano' in pregunta_norm:
            es_americano = personaje.get('nacionalidad') in ['americano', 'mexicana']
            return {'answer': 'Sí' if es_americano else 'No', 'clarification': ''}
        
        # UNIVERSO
        if 'dc' in pregunta_norm:
            es_dc = personaje.get('universo') == 'DC'
            return {'answer': 'Sí' if es_dc else 'No', 'clarification': ''}
        
        if 'marvel' in pregunta_norm:
            es_marvel = personaje.get('universo') == 'Marvel'
            return {'answer': 'Sí' if es_marvel else 'No', 'clarification': ''}
        
        if 'harry potter' in pregunta_norm:
            es_hp = personaje.get('universo') == 'Harry Potter'
            return {'answer': 'Sí' if es_hp else 'No', 'clarification': ''}
        
        # CARACTERÍSTICAS FÍSICAS
        if 'gafas' in pregunta_norm or 'lentes' in pregunta_norm:
            usa_gafas = 'gafas' in ' '.join(personaje.get('caracteristicas', [])).lower()
            return {'answer': 'Sí' if usa_gafas else 'No', 'clarification': ''}
        
        if 'barba' in pregunta_norm:
            tiene_barba = 'barba' in ' '.join(personaje.get('caracteristicas', [])).lower()
            return {'answer': 'Sí' if tiene_barba else 'No', 'clarification': ''}
        
        
        # === NUEVAS PREGUNTAS AGREGADAS EN EL REFACTOR ===
        
        # SIGLO
        if 'siglo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            siglo_inicio = periodo.get('siglo_inicio', 0)
            siglo_fin = periodo.get('siglo_fin', 0)
            
            # Extraer número de siglo de la pregunta si existe
            import re
            match = re.search(r'siglo\s+(\d+)', pregunta_norm)
            if match:
                siglo_preguntado = int(match.group(1))
                if siglo_inicio <= siglo_preguntado <= siglo_fin:
                    return {'answer': 'Sí', 'clarification': ''}
                else:
                    return {'answer': 'No', 'clarification': ''}
            
            # Pregunta genérica sobre siglo
            if siglo_inicio > 0:
                return {'answer': f'Sí, siglo {siglo_inicio}' if siglo_inicio == siglo_fin else f'Siglos {siglo_inicio} al {siglo_fin}', 'clarification': ''}
        
        # ANTES DE CRISTO
        if 'antes de cristo' in pregunta_norm or 'antes cristo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            antes_cristo = periodo.get('antes_de_cristo', False)
            return {'answer': 'Sí' if antes_cristo else 'No', 'clarification': ''}
        
        # PREMIOS / PREMIO NOBEL
        if 'premio nobel' in pregunta_norm or 'nobel' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_nobel = any('nobel' in str(p).lower() for p in premios)
            return {'answer': 'Sí' if tiene_nobel else 'No', 'clarification': ''}
        
        if 'premio' in pregunta_norm and 'nobel' not in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_premios = len(premios) > 0
            return {'answer': 'Sí' if tiene_premios else 'No', 'clarification': ''}
        
        # REVOLUCIONÓ SU CAMPO
        if 'revolucion' in pregunta_norm or 'revoluciono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            revoluciono = impacto.get('revoluciono_campo', False)
            return {'answer': 'Sí' if revoluciono else 'No', 'clarification': ''}
        
        # ICÓNICO / CÉLEBRE
        if 'iconico' in pregunta_norm or 'icono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            iconico = impacto.get('iconico', False)
            return {'answer': 'Sí' if iconico else 'No', 'clarification': ''}
        
        if 'celebre' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            celebre = impacto.get('celebre', False)
            return {'answer': 'Sí' if celebre else 'No', 'clarification': ''}
        
        # PERFIL MORAL
        if 'violento' in pregunta_norm or 'violencia' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            violento = perfil.get('violento', False)
            return {'answer': 'Sí' if violento else 'No', 'clarification': ''}
        
        if 'pacifista' in pregunta_norm or 'paz' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            pacifista = perfil.get('pacifista', False)
            return {'answer': 'Sí' if pacifista else 'No', 'clarification': ''}
        
        if 'conquistador' in pregunta_norm or 'conquisto' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            conquistador = perfil.get('conquistador', False)
            return {'answer': 'Sí' if conquistador else 'No', 'clarification': ''}
        
        if 'imperialista' in pregunta_norm or 'imperio' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            imperialista = perfil.get('imperialista', False)
            return {'answer': 'Sí' if imperialista else 'No', 'clarification': ''}
        
        # ROL
        if 'lider' in pregunta_norm:
            rol = personaje.get('rol', {})
            lider = rol.get('lider', False)
            return {'answer': 'Sí' if lider else 'No', 'clarification': ''}
        
        if 'gobernante' in pregunta_norm or 'goberno' in pregunta_norm:
            rol = personaje.get('rol', {})
            gobernante = rol.get('gobernante', False)
            return {'answer': 'Sí' if gobernante else 'No', 'clarification': ''}
        
        if 'general' in pregunta_norm and 'estadisticas' not in pregunta_norm:
            rol = personaje.get('rol', {})
            general = rol.get('general', False)
            return {'answer': 'Sí' if general else 'No', 'clarification': ''}
        
        if 'antagonista' in pregunta_norm:
            rol = personaje.get('rol', {})
            antagonista = rol.get('antagonista', False)
            return {'answer': 'Sí' if antagonista else 'No', 'clarification': ''}
        
        # === FIN DE NUEVAS PREGUNTAS ===
        

        
        # === NUEVAS PREGUNTAS AGREGADAS EN EL REFACTOR ===
        
        # SIGLO
        if 'siglo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            siglo_inicio = periodo.get('siglo_inicio', 0)
            siglo_fin = periodo.get('siglo_fin', 0)
            
            # Extraer número de siglo de la pregunta si existe
            import re
            match = re.search(r'siglo\s+(\d+)', pregunta_norm)
            if match:
                siglo_preguntado = int(match.group(1))
                if siglo_inicio <= siglo_preguntado <= siglo_fin:
                    return {'answer': 'Sí', 'clarification': ''}
                else:
                    return {'answer': 'No', 'clarification': ''}
            
            # Pregunta genérica sobre siglo
            if siglo_inicio > 0:
                return {'answer': f'Sí, siglo {siglo_inicio}' if siglo_inicio == siglo_fin else f'Siglos {siglo_inicio} al {siglo_fin}', 'clarification': ''}
        
        # ANTES DE CRISTO
        if 'antes de cristo' in pregunta_norm or 'antes cristo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            antes_cristo = periodo.get('antes_de_cristo', False)
            return {'answer': 'Sí' if antes_cristo else 'No', 'clarification': ''}
        
        # PREMIOS / PREMIO NOBEL
        if 'premio nobel' in pregunta_norm or 'nobel' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_nobel = any('nobel' in str(p).lower() for p in premios)
            return {'answer': 'Sí' if tiene_nobel else 'No', 'clarification': ''}
        
        if 'premio' in pregunta_norm and 'nobel' not in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_premios = len(premios) > 0
            return {'answer': 'Sí' if tiene_premios else 'No', 'clarification': ''}
        
        # REVOLUCIONÓ SU CAMPO
        if 'revolucion' in pregunta_norm or 'revoluciono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            revoluciono = impacto.get('revoluciono_campo', False)
            return {'answer': 'Sí' if revoluciono else 'No', 'clarification': ''}
        
        # ICÓNICO / CÉLEBRE
        if 'iconico' in pregunta_norm or 'icono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            iconico = impacto.get('iconico', False)
            return {'answer': 'Sí' if iconico else 'No', 'clarification': ''}
        
        if 'celebre' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            celebre = impacto.get('celebre', False)
            return {'answer': 'Sí' if celebre else 'No', 'clarification': ''}
        
        # PERFIL MORAL
        if 'violento' in pregunta_norm or 'violencia' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            violento = perfil.get('violento', False)
            return {'answer': 'Sí' if violento else 'No', 'clarification': ''}
        
        if 'pacifista' in pregunta_norm or 'paz' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            pacifista = perfil.get('pacifista', False)
            return {'answer': 'Sí' if pacifista else 'No', 'clarification': ''}
        
        if 'conquistador' in pregunta_norm or 'conquisto' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            conquistador = perfil.get('conquistador', False)
            return {'answer': 'Sí' if conquistador else 'No', 'clarification': ''}
        
        if 'imperialista' in pregunta_norm or 'imperio' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            imperialista = perfil.get('imperialista', False)
            return {'answer': 'Sí' if imperialista else 'No', 'clarification': ''}
        
        # ROL
        if 'lider' in pregunta_norm:
            rol = personaje.get('rol', {})
            lider = rol.get('lider', False)
            return {'answer': 'Sí' if lider else 'No', 'clarification': ''}
        
        if 'gobernante' in pregunta_norm or 'goberno' in pregunta_norm:
            rol = personaje.get('rol', {})
            gobernante = rol.get('gobernante', False)
            return {'answer': 'Sí' if gobernante else 'No', 'clarification': ''}
        
        if 'general' in pregunta_norm and 'estadisticas' not in pregunta_norm:
            rol = personaje.get('rol', {})
            general = rol.get('general', False)
            return {'answer': 'Sí' if general else 'No', 'clarification': ''}
        
        if 'antagonista' in pregunta_norm:
            rol = personaje.get('rol', {})
            antagonista = rol.get('antagonista', False)
            return {'answer': 'Sí' if antagonista else 'No', 'clarification': ''}
        
        # === FIN DE NUEVAS PREGUNTAS ===
        

        
        # === NUEVAS PREGUNTAS AGREGADAS EN EL REFACTOR ===
        
        # SIGLO
        if 'siglo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            siglo_inicio = periodo.get('siglo_inicio', 0)
            siglo_fin = periodo.get('siglo_fin', 0)
            
            # Extraer número de siglo de la pregunta si existe
            import re
            match = re.search(r'siglo\s+(\d+)', pregunta_norm)
            if match:
                siglo_preguntado = int(match.group(1))
                if siglo_inicio <= siglo_preguntado <= siglo_fin:
                    return {'answer': 'Sí', 'clarification': ''}
                else:
                    return {'answer': 'No', 'clarification': ''}
            
            # Pregunta genérica sobre siglo
            if siglo_inicio > 0:
                return {'answer': f'Sí, siglo {siglo_inicio}' if siglo_inicio == siglo_fin else f'Siglos {siglo_inicio} al {siglo_fin}', 'clarification': ''}
        
        # ANTES DE CRISTO
        if 'antes de cristo' in pregunta_norm or 'antes cristo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            antes_cristo = periodo.get('antes_de_cristo', False)
            return {'answer': 'Sí' if antes_cristo else 'No', 'clarification': ''}
        
        # PREMIOS / PREMIO NOBEL
        if 'premio nobel' in pregunta_norm or 'nobel' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_nobel = any('nobel' in str(p).lower() for p in premios)
            return {'answer': 'Sí' if tiene_nobel else 'No', 'clarification': ''}
        
        if 'premio' in pregunta_norm and 'nobel' not in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_premios = len(premios) > 0
            return {'answer': 'Sí' if tiene_premios else 'No', 'clarification': ''}
        
        # REVOLUCIONÓ SU CAMPO
        if 'revolucion' in pregunta_norm or 'revoluciono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            revoluciono = impacto.get('revoluciono_campo', False)
            return {'answer': 'Sí' if revoluciono else 'No', 'clarification': ''}
        
        # ICÓNICO / CÉLEBRE
        if 'iconico' in pregunta_norm or 'icono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            iconico = impacto.get('iconico', False)
            return {'answer': 'Sí' if iconico else 'No', 'clarification': ''}
        
        if 'celebre' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            celebre = impacto.get('celebre', False)
            return {'answer': 'Sí' if celebre else 'No', 'clarification': ''}
        
        # PERFIL MORAL
        if 'violento' in pregunta_norm or 'violencia' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            violento = perfil.get('violento', False)
            return {'answer': 'Sí' if violento else 'No', 'clarification': ''}
        
        if 'pacifista' in pregunta_norm or 'paz' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            pacifista = perfil.get('pacifista', False)
            return {'answer': 'Sí' if pacifista else 'No', 'clarification': ''}
        
        if 'conquistador' in pregunta_norm or 'conquisto' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            conquistador = perfil.get('conquistador', False)
            return {'answer': 'Sí' if conquistador else 'No', 'clarification': ''}
        
        if 'imperialista' in pregunta_norm or 'imperio' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            imperialista = perfil.get('imperialista', False)
            return {'answer': 'Sí' if imperialista else 'No', 'clarification': ''}
        
        # ROL
        if 'lider' in pregunta_norm:
            rol = personaje.get('rol', {})
            lider = rol.get('lider', False)
            return {'answer': 'Sí' if lider else 'No', 'clarification': ''}
        
        if 'gobernante' in pregunta_norm or 'goberno' in pregunta_norm:
            rol = personaje.get('rol', {})
            gobernante = rol.get('gobernante', False)
            return {'answer': 'Sí' if gobernante else 'No', 'clarification': ''}
        
        if 'general' in pregunta_norm and 'estadisticas' not in pregunta_norm:
            rol = personaje.get('rol', {})
            general = rol.get('general', False)
            return {'answer': 'Sí' if general else 'No', 'clarification': ''}
        
        if 'antagonista' in pregunta_norm:
            rol = personaje.get('rol', {})
            antagonista = rol.get('antagonista', False)
            return {'answer': 'Sí' if antagonista else 'No', 'clarification': ''}
        
        # === FIN DE NUEVAS PREGUNTAS ===
        

        
        # === NUEVAS PREGUNTAS AGREGADAS EN EL REFACTOR ===
        
        # SIGLO
        if 'siglo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            siglo_inicio = periodo.get('siglo_inicio', 0)
            siglo_fin = periodo.get('siglo_fin', 0)
            
            # Extraer número de siglo de la pregunta si existe
            import re
            match = re.search(r'siglo\s+(\d+)', pregunta_norm)
            if match:
                siglo_preguntado = int(match.group(1))
                if siglo_inicio <= siglo_preguntado <= siglo_fin:
                    return {'answer': 'Sí', 'clarification': ''}
                else:
                    return {'answer': 'No', 'clarification': ''}
            
            # Pregunta genérica sobre siglo
            if siglo_inicio > 0:
                return {'answer': f'Sí, siglo {siglo_inicio}' if siglo_inicio == siglo_fin else f'Siglos {siglo_inicio} al {siglo_fin}', 'clarification': ''}
        
        # ANTES DE CRISTO
        if 'antes de cristo' in pregunta_norm or 'antes cristo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            antes_cristo = periodo.get('antes_de_cristo', False)
            return {'answer': 'Sí' if antes_cristo else 'No', 'clarification': ''}
        
        # PREMIOS / PREMIO NOBEL
        if 'premio nobel' in pregunta_norm or 'nobel' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_nobel = any('nobel' in str(p).lower() for p in premios)
            return {'answer': 'Sí' if tiene_nobel else 'No', 'clarification': ''}
        
        if 'premio' in pregunta_norm and 'nobel' not in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_premios = len(premios) > 0
            return {'answer': 'Sí' if tiene_premios else 'No', 'clarification': ''}
        
        # REVOLUCIONÓ SU CAMPO
        if 'revolucion' in pregunta_norm or 'revoluciono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            revoluciono = impacto.get('revoluciono_campo', False)
            return {'answer': 'Sí' if revoluciono else 'No', 'clarification': ''}
        
        # ICÓNICO / CÉLEBRE
        if 'iconico' in pregunta_norm or 'icono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            iconico = impacto.get('iconico', False)
            return {'answer': 'Sí' if iconico else 'No', 'clarification': ''}
        
        if 'celebre' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            celebre = impacto.get('celebre', False)
            return {'answer': 'Sí' if celebre else 'No', 'clarification': ''}
        
        # PERFIL MORAL
        if 'violento' in pregunta_norm or 'violencia' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            violento = perfil.get('violento', False)
            return {'answer': 'Sí' if violento else 'No', 'clarification': ''}
        
        if 'pacifista' in pregunta_norm or 'paz' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            pacifista = perfil.get('pacifista', False)
            return {'answer': 'Sí' if pacifista else 'No', 'clarification': ''}
        
        if 'conquistador' in pregunta_norm or 'conquisto' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            conquistador = perfil.get('conquistador', False)
            return {'answer': 'Sí' if conquistador else 'No', 'clarification': ''}
        
        if 'imperialista' in pregunta_norm or 'imperio' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            imperialista = perfil.get('imperialista', False)
            return {'answer': 'Sí' if imperialista else 'No', 'clarification': ''}
        
        # ROL
        if 'lider' in pregunta_norm:
            rol = personaje.get('rol', {})
            lider = rol.get('lider', False)
            return {'answer': 'Sí' if lider else 'No', 'clarification': ''}
        
        if 'gobernante' in pregunta_norm or 'goberno' in pregunta_norm:
            rol = personaje.get('rol', {})
            gobernante = rol.get('gobernante', False)
            return {'answer': 'Sí' if gobernante else 'No', 'clarification': ''}
        
        if 'general' in pregunta_norm and 'estadisticas' not in pregunta_norm:
            rol = personaje.get('rol', {})
            general = rol.get('general', False)
            return {'answer': 'Sí' if general else 'No', 'clarification': ''}
        
        if 'antagonista' in pregunta_norm:
            rol = personaje.get('rol', {})
            antagonista = rol.get('antagonista', False)
            return {'answer': 'Sí' if antagonista else 'No', 'clarification': ''}
        
        # === FIN DE NUEVAS PREGUNTAS ===
        

        
        # === NUEVAS PREGUNTAS AGREGADAS EN EL REFACTOR ===
        
        # SIGLO
        if 'siglo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            siglo_inicio = periodo.get('siglo_inicio', 0)
            siglo_fin = periodo.get('siglo_fin', 0)
            
            # Extraer número de siglo de la pregunta si existe
            import re
            match = re.search(r'siglo\s+(\d+)', pregunta_norm)
            if match:
                siglo_preguntado = int(match.group(1))
                if siglo_inicio <= siglo_preguntado <= siglo_fin:
                    return {'answer': 'Sí', 'clarification': ''}
                else:
                    return {'answer': 'No', 'clarification': ''}
            
            # Pregunta genérica sobre siglo
            if siglo_inicio > 0:
                return {'answer': f'Sí, siglo {siglo_inicio}' if siglo_inicio == siglo_fin else f'Siglos {siglo_inicio} al {siglo_fin}', 'clarification': ''}
        
        # ANTES DE CRISTO
        if 'antes de cristo' in pregunta_norm or 'antes cristo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            antes_cristo = periodo.get('antes_de_cristo', False)
            return {'answer': 'Sí' if antes_cristo else 'No', 'clarification': ''}
        
        # PREMIOS / PREMIO NOBEL
        if 'premio nobel' in pregunta_norm or 'nobel' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_nobel = any('nobel' in str(p).lower() for p in premios)
            return {'answer': 'Sí' if tiene_nobel else 'No', 'clarification': ''}
        
        if 'premio' in pregunta_norm and 'nobel' not in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_premios = len(premios) > 0
            return {'answer': 'Sí' if tiene_premios else 'No', 'clarification': ''}
        
        # REVOLUCIONÓ SU CAMPO
        if 'revolucion' in pregunta_norm or 'revoluciono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            revoluciono = impacto.get('revoluciono_campo', False)
            return {'answer': 'Sí' if revoluciono else 'No', 'clarification': ''}
        
        # ICÓNICO / CÉLEBRE
        if 'iconico' in pregunta_norm or 'icono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            iconico = impacto.get('iconico', False)
            return {'answer': 'Sí' if iconico else 'No', 'clarification': ''}
        
        if 'celebre' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            celebre = impacto.get('celebre', False)
            return {'answer': 'Sí' if celebre else 'No', 'clarification': ''}
        
        # PERFIL MORAL
        if 'violento' in pregunta_norm or 'violencia' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            violento = perfil.get('violento', False)
            return {'answer': 'Sí' if violento else 'No', 'clarification': ''}
        
        if 'pacifista' in pregunta_norm or 'paz' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            pacifista = perfil.get('pacifista', False)
            return {'answer': 'Sí' if pacifista else 'No', 'clarification': ''}
        
        if 'conquistador' in pregunta_norm or 'conquisto' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            conquistador = perfil.get('conquistador', False)
            return {'answer': 'Sí' if conquistador else 'No', 'clarification': ''}
        
        if 'imperialista' in pregunta_norm or 'imperio' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            imperialista = perfil.get('imperialista', False)
            return {'answer': 'Sí' if imperialista else 'No', 'clarification': ''}
        
        # ROL
        if 'lider' in pregunta_norm:
            rol = personaje.get('rol', {})
            lider = rol.get('lider', False)
            return {'answer': 'Sí' if lider else 'No', 'clarification': ''}
        
        if 'gobernante' in pregunta_norm or 'goberno' in pregunta_norm:
            rol = personaje.get('rol', {})
            gobernante = rol.get('gobernante', False)
            return {'answer': 'Sí' if gobernante else 'No', 'clarification': ''}
        
        if 'general' in pregunta_norm and 'estadisticas' not in pregunta_norm:
            rol = personaje.get('rol', {})
            general = rol.get('general', False)
            return {'answer': 'Sí' if general else 'No', 'clarification': ''}
        
        if 'antagonista' in pregunta_norm:
            rol = personaje.get('rol', {})
            antagonista = rol.get('antagonista', False)
            return {'answer': 'Sí' if antagonista else 'No', 'clarification': ''}
        
        # === FIN DE NUEVAS PREGUNTAS ===
        

        
        # === NUEVAS PREGUNTAS AGREGADAS EN EL REFACTOR ===
        
        # SIGLO
        if 'siglo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            siglo_inicio = periodo.get('siglo_inicio', 0)
            siglo_fin = periodo.get('siglo_fin', 0)
            
            # Extraer número de siglo de la pregunta si existe
            import re
            match = re.search(r'siglo\s+(\d+)', pregunta_norm)
            if match:
                siglo_preguntado = int(match.group(1))
                if siglo_inicio <= siglo_preguntado <= siglo_fin:
                    return {'answer': 'Sí', 'clarification': ''}
                else:
                    return {'answer': 'No', 'clarification': ''}
            
            # Pregunta genérica sobre siglo
            if siglo_inicio > 0:
                return {'answer': f'Sí, siglo {siglo_inicio}' if siglo_inicio == siglo_fin else f'Siglos {siglo_inicio} al {siglo_fin}', 'clarification': ''}
        
        # ANTES DE CRISTO
        if 'antes de cristo' in pregunta_norm or 'antes cristo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            antes_cristo = periodo.get('antes_de_cristo', False)
            return {'answer': 'Sí' if antes_cristo else 'No', 'clarification': ''}
        
        # PREMIOS / PREMIO NOBEL
        if 'premio nobel' in pregunta_norm or 'nobel' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_nobel = any('nobel' in str(p).lower() for p in premios)
            return {'answer': 'Sí' if tiene_nobel else 'No', 'clarification': ''}
        
        if 'premio' in pregunta_norm and 'nobel' not in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_premios = len(premios) > 0
            return {'answer': 'Sí' if tiene_premios else 'No', 'clarification': ''}
        
        # REVOLUCIONÓ SU CAMPO
        if 'revolucion' in pregunta_norm or 'revoluciono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            revoluciono = impacto.get('revoluciono_campo', False)
            return {'answer': 'Sí' if revoluciono else 'No', 'clarification': ''}
        
        # ICÓNICO / CÉLEBRE
        if 'iconico' in pregunta_norm or 'icono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            iconico = impacto.get('iconico', False)
            return {'answer': 'Sí' if iconico else 'No', 'clarification': ''}
        
        if 'celebre' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            celebre = impacto.get('celebre', False)
            return {'answer': 'Sí' if celebre else 'No', 'clarification': ''}
        
        # PERFIL MORAL
        if 'violento' in pregunta_norm or 'violencia' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            violento = perfil.get('violento', False)
            return {'answer': 'Sí' if violento else 'No', 'clarification': ''}
        
        if 'pacifista' in pregunta_norm or 'paz' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            pacifista = perfil.get('pacifista', False)
            return {'answer': 'Sí' if pacifista else 'No', 'clarification': ''}
        
        if 'conquistador' in pregunta_norm or 'conquisto' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            conquistador = perfil.get('conquistador', False)
            return {'answer': 'Sí' if conquistador else 'No', 'clarification': ''}
        
        if 'imperialista' in pregunta_norm or 'imperio' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            imperialista = perfil.get('imperialista', False)
            return {'answer': 'Sí' if imperialista else 'No', 'clarification': ''}
        
        # ROL
        if 'lider' in pregunta_norm:
            rol = personaje.get('rol', {})
            lider = rol.get('lider', False)
            return {'answer': 'Sí' if lider else 'No', 'clarification': ''}
        
        if 'gobernante' in pregunta_norm or 'goberno' in pregunta_norm:
            rol = personaje.get('rol', {})
            gobernante = rol.get('gobernante', False)
            return {'answer': 'Sí' if gobernante else 'No', 'clarification': ''}
        
        if 'general' in pregunta_norm and 'estadisticas' not in pregunta_norm:
            rol = personaje.get('rol', {})
            general = rol.get('general', False)
            return {'answer': 'Sí' if general else 'No', 'clarification': ''}
        
        if 'antagonista' in pregunta_norm:
            rol = personaje.get('rol', {})
            antagonista = rol.get('antagonista', False)
            return {'answer': 'Sí' if antagonista else 'No', 'clarification': ''}
        
        # === FIN DE NUEVAS PREGUNTAS ===
        

        
        # === NUEVAS PREGUNTAS AGREGADAS EN EL REFACTOR ===
        
        # SIGLO
        if 'siglo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            siglo_inicio = periodo.get('siglo_inicio', 0)
            siglo_fin = periodo.get('siglo_fin', 0)
            
            # Extraer número de siglo de la pregunta si existe
            import re
            match = re.search(r'siglo\s+(\d+)', pregunta_norm)
            if match:
                siglo_preguntado = int(match.group(1))
                if siglo_inicio <= siglo_preguntado <= siglo_fin:
                    return {'answer': 'Sí', 'clarification': ''}
                else:
                    return {'answer': 'No', 'clarification': ''}
            
            # Pregunta genérica sobre siglo
            if siglo_inicio > 0:
                return {'answer': f'Sí, siglo {siglo_inicio}' if siglo_inicio == siglo_fin else f'Siglos {siglo_inicio} al {siglo_fin}', 'clarification': ''}
        
        # ANTES DE CRISTO
        if 'antes de cristo' in pregunta_norm or 'antes cristo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            antes_cristo = periodo.get('antes_de_cristo', False)
            return {'answer': 'Sí' if antes_cristo else 'No', 'clarification': ''}
        
        # PREMIOS / PREMIO NOBEL
        if 'premio nobel' in pregunta_norm or 'nobel' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_nobel = any('nobel' in str(p).lower() for p in premios)
            return {'answer': 'Sí' if tiene_nobel else 'No', 'clarification': ''}
        
        if 'premio' in pregunta_norm and 'nobel' not in pregunta_norm:
            impacto = personaje.get('impacto', {})
            premios = impacto.get('premios', [])
            tiene_premios = len(premios) > 0
            return {'answer': 'Sí' if tiene_premios else 'No', 'clarification': ''}
        
        # REVOLUCIONÓ SU CAMPO
        if 'revolucion' in pregunta_norm or 'revoluciono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            revoluciono = impacto.get('revoluciono_campo', False)
            return {'answer': 'Sí' if revoluciono else 'No', 'clarification': ''}
        
        # ICÓNICO / CÉLEBRE
        if 'iconico' in pregunta_norm or 'icono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            iconico = impacto.get('iconico', False)
            return {'answer': 'Sí' if iconico else 'No', 'clarification': ''}
        
        if 'celebre' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            celebre = impacto.get('celebre', False)
            return {'answer': 'Sí' if celebre else 'No', 'clarification': ''}
        
        # PERFIL MORAL
        if 'violento' in pregunta_norm or 'violencia' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            violento = perfil.get('violento', False)
            return {'answer': 'Sí' if violento else 'No', 'clarification': ''}
        
        if 'pacifista' in pregunta_norm or 'paz' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            pacifista = perfil.get('pacifista', False)
            return {'answer': 'Sí' if pacifista else 'No', 'clarification': ''}
        
        if 'conquistador' in pregunta_norm or 'conquisto' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            conquistador = perfil.get('conquistador', False)
            return {'answer': 'Sí' if conquistador else 'No', 'clarification': ''}
        
        if 'imperialista' in pregunta_norm or 'imperio' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            imperialista = perfil.get('imperialista', False)
            return {'answer': 'Sí' if imperialista else 'No', 'clarification': ''}
        
        # ROL
        if 'lider' in pregunta_norm:
            rol = personaje.get('rol', {})
            lider = rol.get('lider', False)
            return {'answer': 'Sí' if lider else 'No', 'clarification': ''}
        
        if 'gobernante' in pregunta_norm or 'goberno' in pregunta_norm:
            rol = personaje.get('rol', {})
            gobernante = rol.get('gobernante', False)
            return {'answer': 'Sí' if gobernante else 'No', 'clarification': ''}
        
        if 'general' in pregunta_norm and 'estadisticas' not in pregunta_norm:
            rol = personaje.get('rol', {})
            general = rol.get('general', False)
            return {'answer': 'Sí' if general else 'No', 'clarification': ''}
        
        if 'antagonista' in pregunta_norm:
            rol = personaje.get('rol', {})
            antagonista = rol.get('antagonista', False)
            return {'answer': 'Sí' if antagonista else 'No', 'clarification': ''}
        
        # === FIN DE NUEVAS PREGUNTAS ===
        

        # NO CLASIFICABLE
        return {'answer': 'No lo sé', 'clarification': 'No estoy seguro de cómo interpretar eso. ¿Podrías reformularlo?'}


# ===================================================================
# GENERADOR DE SUGERENCIAS MEJORADO
# ===================================================================

class GeneradorSugerencias:
    """Genera sugerencias ÚTILES basadas en lo que se conoce"""
    
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
        "¿Es detective?"
    ]
    
    @staticmethod
    def generar(preguntas_hechas: List[str], max_sugerencias: int = 5) -> List[str]:
        """Genera sugerencias que NO hayan sido preguntadas"""
        
        # Normalizar preguntas hechas
        preguntas_norm = [Normalizador.normalizar(p) for p in preguntas_hechas]
        
        sugerencias_disponibles = []
        
        for sugerencia in GeneradorSugerencias.SUGERENCIAS_BASE:
            sug_norm = Normalizador.normalizar(sugerencia)
            
            # Verificar si ya fue preguntada
            ya_preguntada = False
            for p_norm in preguntas_norm:
                # Verificar si comparten palabras clave
                palabras_sug = set(sug_norm.split())
                palabras_preg = set(p_norm.split())
                
                # Si comparten 2+ palabras significativas, considerar como ya preguntada
                palabras_comunes = palabras_sug & palabras_preg
                if len(palabras_comunes) >= 2:
                    ya_preguntada = True
                    break
            
            if not ya_preguntada:
                sugerencias_disponibles.append(sugerencia)
            
            # Si ya tenemos suficientes
            if len(sugerencias_disponibles) >= max_sugerencias * 2:
                break
        
        # Retornar solo las que pedimos
        return sugerencias_disponibles[:max_sugerencias]


# ===================================================================
# SISTEMA DE HUECOS
# ===================================================================

def registrar_hueco(pregunta: str, personaje: Dict, pregunta_norm: str):
    """Registra preguntas no respondidas"""
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
        
        # Registrar en métricas
        metricas_manager.registrar_hueco_categoria("pregunta_no_clasificable")
            
        print(f"📝 Hueco registrado: '{pregunta}' para {personaje.get('nombre')}")
    except Exception as e:
        print(f"⚠️ Error registrando hueco: {e}")
        metricas_manager.registrar_error(str(e), "registrar_hueco")


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
        
        # Registrar en métricas globales
        metricas_manager.registrar_pregunta(pregunta)
    
    def puede_seguir(self) -> bool:
        return self.preguntas_restantes > 0
    
    def finalizar(self, ganado: bool):
        """Marca el fin de la partida"""
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
            
            # Registrar inicio en métricas
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
            
            # Obtener memoria
            if session_id not in memorias:
                memorias[session_id] = MemoriaPartida(character.get('nombre', 'desconocido'))
            
            memoria = memorias[session_id]
            
            if not memoria.puede_seguir():
                memoria.finalizar(False)
                return jsonify({'answer': 'Has agotado tus preguntas. Debes adivinar.', 'clarification': ''})
            
            # Analizar pregunta
            respuesta = analizador.analizar(question, character)
            
            # Registrar hueco si corresponde
            if respuesta['answer'] == 'No lo sé':
                registrar_hueco(question, character, Normalizador.normalizar(question))
            
            # Registrar en memoria
            memoria.registrar(question, respuesta['answer'])
            
            return jsonify(respuesta)
        
        elif action == 'guess':
            guess = data.get('guess', '').lower().strip()
            character = data.get('character', {})
            character_name = character.get('nombre', '').lower().strip()
            
            guess_norm = Normalizador.normalizar(guess)
            name_norm = Normalizador.normalizar(character_name)
            
            correct = guess_norm == name_norm
            
            # Finalizar partida
            if session_id in memorias:
                memorias[session_id].finalizar(correct)
            
            return jsonify({'correct': correct, 'character': character['nombre']})
        
        elif action == 'suggestions':
            # Obtener preguntas hechas
            if session_id in memorias:
                preguntas_hechas = memorias[session_id].preguntas
            else:
                preguntas_hechas = []
            
            suggestions = generador.generar(preguntas_hechas, max_sugerencias=5)
            
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



# ===================================================================
# GENERADOR DE REPORTES
# ===================================================================

class GeneradorReportes:
    """Genera reportes de dashboard en diferentes formatos"""
    
    @staticmethod
    def generar_txt() -> str:
        """Genera reporte en formato TXT"""
        
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
        
        # Header
        output.write("=" * 80 + "\n")
        output.write("THE ORACLE - REPORTE DE DASHBOARD\n")
        output.write("=" * 80 + "\n")
        output.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write("=" * 80 + "\n\n")
        
        # Estadísticas Generales
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
        
        # Personajes más jugados
        output.write("PERSONAJES MÁS JUGADOS (Top 20)\n")
        output.write("-" * 80 + "\n")
        personajes_usados = metricas.get('personajes_usados', {})
        personajes_sorted = sorted(personajes_usados.items(), key=lambda x: x[1], reverse=True)
        
        for i, (nombre, veces) in enumerate(personajes_sorted[:20], 1):
            output.write(f"{i:2d}. {nombre:30s} - {veces:3d} veces\n")
        output.write("\n")
        
        # Tasa de éxito por personaje
        output.write("TASA DE ÉXITO POR PERSONAJE\n")
        output.write("-" * 80 + "\n")
        output.write(f"{'Personaje':<30} {'Usadas':<8} {'Ganadas':<8} {'Perdidas':<8} {'% Victoria':<10}\n")
        output.write("-" * 80 + "\n")
        
        tasa_exito = metricas.get('tasa_exito_por_personaje', {})
        for personaje, stats in sorted(tasa_exito.items(), key=lambda x: x[1].get('ganadas', 0) + x[1].get('perdidas', 0), reverse=True):
            ganadas = stats.get('ganadas', 0)
            perdidas = stats.get('perdidas', 0)
            total_p = ganadas + perdidas
            porcentaje = (ganadas / total_p * 100) if total_p > 0 else 0
            usado = personajes_usados.get(personaje, total_p)
            
            output.write(f"{personaje:<30} {usado:<8} {ganadas:<8} {perdidas:<8} {porcentaje:<10.2f}\n")
        output.write("\n")
        
        # Huecos
        output.write("ANÁLISIS DE HUECOS\n")
        output.write("-" * 80 + "\n")
        output.write(f"Total de Huecos: {len(huecos)}\n\n")
        
        # Preguntas más frecuentes
        from collections import Counter
        preguntas_counter = Counter([h['pregunta_normalizada'] for h in huecos])
        output.write("Top 30 Preguntas Más Frecuentes (Sin Respuesta):\n")
        output.write("-" * 80 + "\n")
        
        for i, (pregunta, cantidad) in enumerate(preguntas_counter.most_common(30), 1):
            output.write(f"{i:2d}. [{cantidad:3d}x] {pregunta}\n")
        output.write("\n")
        
        # Personajes problemáticos
        personajes_counter = Counter([h['personaje'] for h in huecos])
        output.write("Top 15 Personajes con Más Huecos:\n")
        output.write("-" * 80 + "\n")
        
        for i, (personaje, cantidad) in enumerate(personajes_counter.most_common(15), 1):
            output.write(f"{i:2d}. {personaje:30s} - {cantidad:3d} huecos\n")
        output.write("\n")
        
        # Últimos huecos
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
        
        # Footer
        output.write("=" * 80 + "\n")
        output.write("FIN DEL REPORTE\n")
        output.write("=" * 80 + "\n")
        
        return output.getvalue()




@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Obtiene estadísticas generales"""
    try:
        stats = metricas_manager.obtener_estadisticas()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/huecos', methods=['GET'])
def dashboard_huecos():
    """Obtiene lista de huecos"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        if os.path.exists(REGISTRO_HUECOS_FILE):
            with open(REGISTRO_HUECOS_FILE, 'r', encoding='utf-8') as f:
                huecos = json.load(f)
            
            # Analizar patrones
            preguntas_counter = Counter([h['pregunta_normalizada'] for h in huecos])
            personajes_counter = Counter([h['personaje'] for h in huecos])
            
            return jsonify({
                'total': len(huecos),
                'ultimos': huecos[-limit:],
                'preguntas_frecuentes': preguntas_counter.most_common(20),
                'personajes_problematicos': personajes_counter.most_common(10)
            })
        else:
            return jsonify({
                'total': 0,
                'ultimos': [],
                'preguntas_frecuentes': [],
                'personajes_problematicos': []
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/personajes', methods=['GET'])
def dashboard_personajes():
    """Obtiene estadísticas de personajes"""
    try:
        personajes_stats = []
        
        for p in PERSONAJES:
            nombre = p['nombre']
            veces_usado = metricas_manager.metricas['personajes_usados'].get(nombre, 0)
            
            tasa_exito = metricas_manager.metricas['tasa_exito_por_personaje'].get(nombre, {"ganadas": 0, "perdidas": 0})
            total_partidas = tasa_exito['ganadas'] + tasa_exito['perdidas']
            porcentaje_victoria = round(tasa_exito['ganadas'] / total_partidas * 100, 2) if total_partidas > 0 else 0
            
            personajes_stats.append({
                'nombre': nombre,
                'tipo': p['tipo'],
                'veces_usado': veces_usado,
                'partidas_ganadas': tasa_exito['ganadas'],
                'partidas_perdidas': tasa_exito['perdidas'],
                'porcentaje_victoria': porcentaje_victoria
            })
        
        # Ordenar por veces usado
        personajes_stats.sort(key=lambda x: x['veces_usado'], reverse=True)
        
        return jsonify({
            'personajes': personajes_stats,
            'total_personajes': len(PERSONAJES)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/errores', methods=['GET'])
def dashboard_errores():
    """Obtiene lista de errores del sistema"""
    try:
        limit = request.args.get('limit', 50, type=int)
        errores = metricas_manager.metricas.get('errores', [])
        
        return jsonify({
            'total': len(errores),
            'ultimos': errores[-limit:]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        
        .progress-bar {
            width: 100%;
            height: 25px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 12px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff00, #ff00ff);
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-weight: bold;
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
            h1 {
                font-size: 2em;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .tabs {
                flex-direction: column;
            }
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
        
        <!-- TAB GENERAL -->
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
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Personaje</th>
                            <th>Veces Usado</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="3" class="loading">Cargando...</td></tr>
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>🎲 Personajes Menos Jugados</h2>
                <table id="table-menos-usados">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Personaje</th>
                            <th>Veces Usado</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="3" class="loading">Cargando...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- TAB PERSONAJES -->
        <div id="tab-personajes" class="tab-content">
            <div class="section">
                <h2>🎭 Estadísticas por Personaje</h2>
                <table id="table-personajes">
                    <thead>
                        <tr>
                            <th>Personaje</th>
                            <th>Tipo</th>
                            <th>Veces Usado</th>
                            <th>Ganadas</th>
                            <th>Perdidas</th>
                            <th>% Victoria</th>
                            <th>Dificultad</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="7" class="loading">Cargando...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- TAB HUECOS -->
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
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Pregunta</th>
                            <th>Ocurrencias</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="3" class="loading">Cargando...</td></tr>
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>🎭 Personajes con Más Huecos</h2>
                <table id="table-personajes-problematicos">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Personaje</th>
                            <th>Huecos Registrados</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="3" class="loading">Cargando...</td></tr>
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>📝 Últimos Huecos Registrados</h2>
                <table id="table-huecos-recientes">
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Pregunta Original</th>
                            <th>Personaje</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="3" class="loading">Cargando...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- TAB ERRORES -->
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
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Error</th>
                            <th>Contexto</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="3" class="loading">Cargando...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {
            // Ocultar todos los tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Desactivar todos los botones
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Activar tab y botón seleccionados
            document.getElementById('tab-' + tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        async function loadGeneralStats() {
            try {
                const response = await fetch('/api/dashboard/stats');
                const data = await response.json();
                
                document.getElementById('stat-partidas').textContent = data.partidas_totales;
                document.getElementById('stat-ganadas').textContent = data.partidas_ganadas;
                document.getElementById('stat-tasa').textContent = data.tasa_victoria + '%';
                document.getElementById('stat-preguntas').textContent = data.preguntas_totales;
                
                // Personajes más usados
                const tbody1 = document.querySelector('#table-mas-usados tbody');
                tbody1.innerHTML = data.personajes_mas_usados.map((p, i) => `
                    <tr>
                        <td>${i + 1}</td>
                        <td>${p[0]}</td>
                        <td>${p[1]}</td>
                    </tr>
                `).join('') || '<tr><td colspan="3" class="empty-state">No hay datos</td></tr>';
                
                // Personajes menos usados
                const tbody2 = document.querySelector('#table-menos-usados tbody');
                tbody2.innerHTML = data.personajes_menos_usados.map((p, i) => `
                    <tr>
                        <td>${i + 1}</td>
                        <td>${p[0]}</td>
                        <td>${p[1]}</td>
                    </tr>
                `).join('') || '<tr><td colspan="3" class="empty-state">No hay datos</td></tr>';
            } catch (error) {
                console.error('Error cargando stats:', error);
            }
        }
        
        async function loadPersonajes() {
            try {
                const response = await fetch('/api/dashboard/personajes');
                const data = await response.json();
                
                const tbody = document.querySelector('#table-personajes tbody');
                tbody.innerHTML = data.personajes.map(p => {
                    let dificultad = 'Normal';
                    if (p.porcentaje_victoria > 70) dificultad = 'Fácil';
                    else if (p.porcentaje_victoria < 30) dificultad = 'Difícil';
                    
                    return `
                        <tr>
                            <td>${p.nombre}</td>
                            <td><span class="badge ${p.tipo === 'real' ? 'badge-success' : 'badge-warning'}">${p.tipo}</span></td>
                            <td>${p.veces_usado}</td>
                            <td>${p.partidas_ganadas}</td>
                            <td>${p.partidas_perdidas}</td>
                            <td>${p.porcentaje_victoria}%</td>
                            <td>${dificultad}</td>
                        </tr>
                    `;
                }).join('') || '<tr><td colspan="7" class="empty-state">No hay datos</td></tr>';
            } catch (error) {
                console.error('Error cargando personajes:', error);
            }
        }
        
        async function loadHuecos() {
            try {
                const response = await fetch('/api/dashboard/huecos');
                const data = await response.json();
                
                document.getElementById('stat-huecos-total').textContent = data.total;
                
                // Preguntas frecuentes
                const tbody1 = document.querySelector('#table-huecos-frecuentes tbody');
                tbody1.innerHTML = data.preguntas_frecuentes.map((p, i) => `
                    <tr>
                        <td>${i + 1}</td>
                        <td>${p[0]}</td>
                        <td><span class="badge badge-error">${p[1]}</span></td>
                    </tr>
                `).join('') || '<tr><td colspan="3" class="empty-state">No hay huecos registrados</td></tr>';
                
                // Personajes problemáticos
                const tbody2 = document.querySelector('#table-personajes-problematicos tbody');
                tbody2.innerHTML = data.personajes_problematicos.map((p, i) => `
                    <tr>
                        <td>${i + 1}</td>
                        <td>${p[0]}</td>
                        <td><span class="badge badge-warning">${p[1]}</span></td>
                    </tr>
                `).join('') || '<tr><td colspan="3" class="empty-state">No hay datos</td></tr>';
                
                // Últimos huecos
                const tbody3 = document.querySelector('#table-huecos-recientes tbody');
                tbody3.innerHTML = data.ultimos.reverse().slice(0, 30).map(h => `
                    <tr>
                        <td>${new Date(h.timestamp).toLocaleString()}</td>
                        <td>${h.pregunta_original}</td>
                        <td>${h.personaje}</td>
                    </tr>
                `).join('') || '<tr><td colspan="3" class="empty-state">No hay huecos registrados</td></tr>';
            } catch (error) {
                console.error('Error cargando huecos:', error);
            }
        }
        
        async function loadErrores() {
            try {
                const response = await fetch('/api/dashboard/errores');
                const data = await response.json();
                
                document.getElementById('stat-errores-total').textContent = data.total;
                
                const tbody = document.querySelector('#table-errores tbody');
                tbody.innerHTML = data.ultimos.reverse().map(e => `
                    <tr>
                        <td>${new Date(e.timestamp).toLocaleString()}</td>
                        <td><span class="badge badge-error">${e.error}</span></td>
                        <td>${e.contexto}</td>
                    </tr>
                `).join('') || '<tr><td colspan="3" class="empty-state">No hay errores registrados</td></tr>';
            } catch (error) {
                console.error('Error cargando errores:', error);
            }
        }
        
        async function loadAllData() {
            await Promise.all([
                loadGeneralStats(),
                loadPersonajes(),
                loadHuecos(),
                loadErrores()
            ]);
        }
        
        
        function exportarTXT() {
            window.location.href = '/api/dashboard/exportar-txt';
        }
        
        // Cargar datos al iniciar
        loadAllData();
        
        // Auto-refresh cada 30 segundos
        setInterval(loadAllData, 30000);
    </script>
</body>
</html>
'''


@app.route('/dashboard')
def dashboard():
    """Panel de control HTML"""
    return render_template_string(DASHBOARD_HTML)


# ===================================================================
# ENDPOINTS BÁSICOS
# ===================================================================



@app.route('/api/dashboard/exportar-txt', methods=['GET'])
def exportar_txt():
    """Exporta el reporte del dashboard en formato TXT"""
    try:
        txt_content = GeneradorReportes.generar_txt()
        
        response = make_response(txt_content)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=oracle_dashboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        <p>20 Personajes | Sistema FUNCIONAL</p>
        <p>✅ Respuestas CORRECTAS</p>
        <p>✅ Sugerencias ÚTILES</p>
        <p>✅ Panel de Control Activo</p>
        <br>
        <a href="/dashboard" style="color:#00ff00; font-size:1.5em;">📊 Ver Dashboard</a>
    </body>
    </html>
    """


if __name__ == '__main__':
    import os
    print("=" * 60)
    print("🧠 THE ORACLE - Backend con Dashboard")
    print("=" * 60)
    print(f"📡 Servidor: http://0.0.0.0:5000")
    print(f"🎭 Personajes: {len(PERSONAJES)}")
    print(f"📊 Dashboard: http://0.0.0.0:5000/dashboard")
    print("✅ Sistema de métricas ACTIVADO")
    print("✅ Registro automático de estadísticas")
    print("=" * 60)
    
    # Puerto para producción
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
