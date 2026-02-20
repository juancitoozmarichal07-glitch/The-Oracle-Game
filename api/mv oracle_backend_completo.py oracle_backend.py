#!/usr/bin/env python3
"""
THE ORACLE - Backend COMPLETO con 50 Personajes
Versión: 3.0 - Cobertura de Huecos + Carga desde JSON
- ✅ Carga personajes desde personajes.json
- ✅ 50 personajes con campos expandidos
- ✅ Cobertura de 30+ nuevas preguntas
- ✅ Dashboard completo con métricas
- ✅ Sistema de huecos integrado
- ✅ Exportación a TXT
"""

from flask import Flask, request, jsonify, render_template_string, send_file, make_response
from flask_cors import CORS
from io import BytesIO, StringIO
from collections import Counter, defaultdict
import random
import unicodedata
import json
import os
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
# CARGADOR DE PERSONAJES DESDE JSON
# ===================================================================

def cargar_personajes(archivo: str = PERSONAJES_FILE) -> List[Dict]:
    """
    Carga personajes desde archivo JSON externo.
    
    Fallback: Si no existe el archivo, retorna array vacío.
    El servidor mostrará error claro si no hay personajes.
    """
    try:
        if os.path.exists(archivo):
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                personajes = data.get('personajes', [])
                print(f"✅ {len(personajes)} personajes cargados desde {archivo}")
                return personajes
        else:
            print(f"⚠️  Archivo {archivo} no encontrado")
            return []
    except Exception as e:
        print(f"❌ Error cargando personajes: {e}")
        return []


# Cargar personajes desde archivo JSON
PERSONAJES = cargar_personajes()

# Validación: Verificar que se cargaron personajes
if not PERSONAJES:
    print("=" * 60)
    print("⚠️  ADVERTENCIA: No se cargaron personajes")
    print("Asegúrate de que personajes.json existe en el mismo directorio")
    print("=" * 60)


# ===================================================================
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
            'partidas_totales': 0,
            'partidas_ganadas': 0,
            'partidas_perdidas': 0,
            'preguntas_totales': 0,
            'personajes_usados': {},
            'tasa_exito_por_personaje': {},
            'huecos_por_categoria': {},
            'errores': []
        }
    
    def guardar_metricas(self):
        """Guarda métricas a archivo"""
        try:
            with open(METRICAS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.metricas, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error guardando métricas: {e}")
    
    def registrar_partida(self, personaje: str, ganada: bool, preguntas: int):
        """Registra una partida jugada"""
        self.metricas['partidas_totales'] += 1
        if ganada:
            self.metricas['partidas_ganadas'] += 1
        else:
            self.metricas['partidas_perdidas'] += 1
        
        self.metricas['preguntas_totales'] += preguntas
        
        # Incrementar contador de personaje
        if personaje not in self.metricas['personajes_usados']:
            self.metricas['personajes_usados'][personaje] = 0
        self.metricas['personajes_usados'][personaje] += 1
        
        # Actualizar tasa de éxito
        if personaje not in self.metricas['tasa_exito_por_personaje']:
            self.metricas['tasa_exito_por_personaje'][personaje] = {
                'ganadas': 0,
                'perdidas': 0
            }
        
        if ganada:
            self.metricas['tasa_exito_por_personaje'][personaje]['ganadas'] += 1
        else:
            self.metricas['tasa_exito_por_personaje'][personaje]['perdidas'] += 1
        
        self.guardar_metricas()
    
    def registrar_error(self, error: str, contexto: str = ""):
        """Registra un error del sistema"""
        if 'errores' not in self.metricas:
            self.metricas['errores'] = []
        
        self.metricas['errores'].append({
            'timestamp': datetime.now().isoformat(),
            'error': error,
            'contexto': contexto
        })
        
        # Mantener solo los últimos 100 errores
        self.metricas['errores'] = self.metricas['errores'][-100:]
        self.guardar_metricas()

metricas_manager = MetricasManager()


# ===================================================================
# NORMALIZADOR DE TEXTO
# ===================================================================

class Normalizador:
    """Normaliza texto para comparación consistente"""
    
    @staticmethod
    def normalizar(texto: str) -> str:
        """
        Normaliza texto:
        - Lowercase
        - Sin acentos
        - Sin puntuación extra
        """
        if not texto:
            return ""
        
        # Lowercase
        texto = texto.lower()
        
        # Remover acentos
        texto = ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Remover signos de interrogación y exclamación
        texto = texto.replace('¿', '').replace('?', '')
        texto = texto.replace('¡', '').replace('!', '')
        
        # Remover puntuación extra pero mantener espacios
        texto = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in texto)
        
        # Normalizar espacios múltiples
        texto = ' '.join(texto.split())
        
        return texto.strip()


# ===================================================================
# REGISTRO DE HUECOS
# ===================================================================

class RegistroHuecos:
    """Registra preguntas no respondidas"""
    
    @staticmethod
    def registrar(pregunta: str, pregunta_normalizada: str, personaje: str):
        """Registra un hueco en el diccionario"""
        try:
            # Cargar huecos existentes
            huecos = []
            if os.path.exists(REGISTRO_HUECOS_FILE):
                with open(REGISTRO_HUECOS_FILE, 'r', encoding='utf-8') as f:
                    huecos = json.load(f)
            
            # Agregar nuevo hueco
            huecos.append({
                'timestamp': datetime.now().isoformat(),
                'pregunta_original': pregunta,
                'pregunta_normalizada': pregunta_normalizada,
                'personaje': personaje
            })
            
            # Guardar
            with open(REGISTRO_HUECOS_FILE, 'w', encoding='utf-8') as f:
                json.dump(huecos, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"Error registrando hueco: {e}")


# ===================================================================
# ANALIZADOR DE PREGUNTAS
# ===================================================================

class AnalizadorPreguntas:
    """Analiza y responde preguntas sobre personajes"""
    
    def __init__(self):
        self.normalizador = Normalizador()
    
    def analizar(self, pregunta: str, personaje: Dict) -> Dict[str, str]:
        """
        Analiza una pregunta y retorna la respuesta.
        
        Returns:
            Dict con 'answer' y 'clarification'
        """
        pregunta_norm = self.normalizador.normalizar(pregunta)
        
        # === TIPO DE PERSONAJE ===
        if any(palabra in pregunta_norm for palabra in ['real', 'existio', 'historico', 'carne y hueso']):
            es_real = personaje.get('tipo') == 'real'
            return {'answer': 'Sí' if es_real else 'No', 'clarification': ''}
        
        if any(palabra in pregunta_norm for palabra in ['ficticio', 'inventado', 'imaginario']):
            es_ficticio = personaje.get('tipo') == 'ficticio'
            return {'answer': 'Sí' if es_ficticio else 'No', 'clarification': ''}
        
        # === SER IMAGINARIO (sinónimo de ficticio) ===
        if 'ser imaginario' in pregunta_norm or 'es imaginario' in pregunta_norm:
            tipo = personaje.get('tipo', 'real')
            return {'answer': 'Sí' if tipo == 'ficticio' else 'No', 'clarification': ''}
        
        # === GÉNERO ===
        if any(palabra in pregunta_norm for palabra in ['hombre', 'varon', 'masculino']):
            es_hombre = personaje.get('genero') == 'masculino'
            return {'answer': 'Sí' if es_hombre else 'No', 'clarification': ''}
        
        if any(palabra in pregunta_norm for palabra in ['mujer', 'femenino', 'femenina']):
            es_mujer = personaje.get('genero') == 'femenino'
            return {'answer': 'Sí' if es_mujer else 'No', 'clarification': ''}
        
        # === DAMA (sinónimo de mujer) ===
        if 'dama' in pregunta_norm or 'es una dama' in pregunta_norm:
            genero = personaje.get('genero', '')
            return {'answer': 'Sí' if genero == 'femenino' else 'No', 'clarification': ''}
        
        # === ESTADO VITAL ===
        if any(palabra in pregunta_norm for palabra in ['vivo', 'vive', 'sigue vivo']):
            esta_vivo = personaje.get('vivo', False)
            return {'answer': 'Sí' if esta_vivo else 'No', 'clarification': ''}
        
        if any(palabra in pregunta_norm for palabra in ['muerto', 'fallecido', 'fallecida', 'murio']):
            esta_muerto = not personaje.get('vivo', True)
            return {'answer': 'Sí' if esta_muerto else 'No', 'clarification': ''}
        
        # === FALLECIDO / PERSONA FALLECIDA ===
        if 'fallecido' in pregunta_norm or 'fallecida' in pregunta_norm or 'persona fallecida' in pregunta_norm:
            vivo = personaje.get('vivo', True)
            return {'answer': 'Sí' if not vivo else 'No', 'clarification': ''}
        
        # === FAMA ===
        if any(palabra in pregunta_norm for palabra in ['famoso', 'conocido', 'celebre']):
            es_famoso = personaje.get('famoso', False)
            return {'answer': 'Sí' if es_famoso else 'No', 'clarification': ''}
        
        # === RIQUEZA ===
        if any(palabra in pregunta_norm for palabra in ['rico', 'adinerado', 'millonario']):
            es_rico = personaje.get('rico', False)
            return {'answer': 'Sí' if es_rico else 'No', 'clarification': ''}
        
        # === MUCHO DINERO ===
        if 'mucho dinero' in pregunta_norm or 'millonario' in pregunta_norm or 'adinerado' in pregunta_norm:
            rico = personaje.get('rico', False)
            return {'answer': 'Sí' if rico else 'No', 'clarification': ''}
        
        # === POBRE ===
        if 'pobre' in pregunta_norm or 'pobreza' in pregunta_norm:
            pobre = personaje.get('pobre', False)
            return {'answer': 'Sí' if pobre else 'No', 'clarification': ''}
        
        # === NACIONALIDAD - CONTINENTES ===
        if any(palabra in pregunta_norm for palabra in ['europeo', 'europa']):
            nacionalidades_europeas = ['aleman', 'frances', 'italiano', 'ingles', 'britanico', 
                                      'espanol', 'polaco', 'ruso', 'griego', 'romano']
            nacionalidad = personaje.get('nacionalidad', '').lower()
            return {'answer': 'Sí' if any(n in nacionalidad for n in nacionalidades_europeas) else 'No', 'clarification': ''}
        
        if any(palabra in pregunta_norm for palabra in ['americano', 'america', 'estadounidense']):
            nacionalidades_americanas = ['americano', 'estadounidense', 'mexicano', 'venezolano']
            nacionalidad = personaje.get('nacionalidad', '').lower()
            return {'answer': 'Sí' if any(n in nacionalidad for n in nacionalidades_americanas) else 'No', 'clarification': ''}
        
        if any(palabra in pregunta_norm for palabra in ['asiatico', 'asia']):
            nacionalidades_asiaticas = ['chino', 'japones', 'indio', 'coreano']
            nacionalidad = personaje.get('nacionalidad', '').lower()
            return {'answer': 'Sí' if any(n in nacionalidad for n in nacionalidades_asiaticas) else 'No', 'clarification': ''}
        
        # === NACIONALIDADES ESPECÍFICAS ===
        if 'aleman' in pregunta_norm or 'alemania' in pregunta_norm:
            nacionalidad = personaje.get('nacionalidad', '').lower()
            return {'answer': 'Sí' if 'aleman' in nacionalidad else 'No', 'clarification': ''}
        
        if 'polaco' in pregunta_norm or 'polonia' in pregunta_norm:
            nacionalidad = personaje.get('nacionalidad', '').lower()
            return {'answer': 'Sí' if 'polac' in nacionalidad else 'No', 'clarification': ''}
        
        if 'chino' in pregunta_norm or 'china' in pregunta_norm:
            nacionalidad = personaje.get('nacionalidad', '').lower()
            return {'answer': 'Sí' if 'chin' in nacionalidad else 'No', 'clarification': ''}
        
        if 'ingles' in pregunta_norm or 'britanico' in pregunta_norm or 'inglaterra' in pregunta_norm:
            nacionalidad = personaje.get('nacionalidad', '').lower()
            return {'answer': 'Sí' if 'ingles' in nacionalidad or 'britanico' in nacionalidad else 'No', 'clarification': ''}
        
        if 'frances' in pregunta_norm or 'francia' in pregunta_norm:
            nacionalidad = personaje.get('nacionalidad', '').lower()
            return {'answer': 'Sí' if 'frances' in nacionalidad else 'No', 'clarification': ''}
        
        if 'espanol' in pregunta_norm or 'espana' in pregunta_norm:
            nacionalidad = personaje.get('nacionalidad', '').lower()
            return {'answer': 'Sí' if 'espanol' in nacionalidad else 'No', 'clarification': ''}
        
        if 'estadounidense' in pregunta_norm or 'usa' in pregunta_norm or 'estados unidos' in pregunta_norm:
            nacionalidad = personaje.get('nacionalidad', '').lower()
            return {'answer': 'Sí' if 'estadounidense' in nacionalidad or 'americano' in nacionalidad else 'No', 'clarification': ''}
        
        # === PROFESIÓN ===
        if any(palabra in pregunta_norm for palabra in ['cientifico', 'cientifica']):
            es_cientifico = personaje.get('profesion', '').lower() in ['cientifico', 'cientifica']
            return {'answer': 'Sí' if es_cientifico else 'No', 'clarification': ''}
        
        if any(palabra in pregunta_norm for palabra in ['artista', 'pintor', 'escultor']):
            profesion = personaje.get('profesion', '').lower()
            es_artista = profesion == 'artista' or 'arte' in personaje.get('area', '').lower()
            return {'answer': 'Sí' if es_artista else 'No', 'clarification': ''}
        
        if any(palabra in pregunta_norm for palabra in ['escritor', 'autor']):
            es_escritor = personaje.get('profesion', '').lower() == 'escritor'
            return {'answer': 'Sí' if es_escritor else 'No', 'clarification': ''}
        
        if any(palabra in pregunta_norm for palabra in ['militar', 'soldado', 'guerrero', 'guerrera']):
            profesion = personaje.get('profesion', '').lower()
            es_militar = profesion in ['militar', 'guerrera', 'guerrero']
            return {'answer': 'Sí' if es_militar else 'No', 'clarification': ''}
        
        if any(palabra in pregunta_norm for palabra in ['politico', 'politica']):
            area = personaje.get('area', '').lower()
            es_politico = 'politica' in area or personaje.get('profesion', '').lower() in ['lider', 'reina', 'presidente']
            return {'answer': 'Sí' if es_politico else 'No', 'clarification': ''}
        
        # === ÉPOCA ===
        if any(palabra in pregunta_norm for palabra in ['antigua', 'antiguedad']):
            epoca = personaje.get('epoca', '').lower()
            return {'answer': 'Sí' if 'antigua' in epoca else 'No', 'clarification': ''}
        
        if any(palabra in pregunta_norm for palabra in ['moderna', 'contemporaneo']):
            epoca = personaje.get('epoca', '').lower()
            return {'answer': 'Sí' if 'moderna' in epoca else 'No', 'clarification': ''}
        
        if any(palabra in pregunta_norm for palabra in ['renacimiento']):
            epoca = personaje.get('epoca', '').lower()
            periodo = personaje.get('periodo', {})
            es_renacimiento = 'renacimiento' in epoca or periodo.get('es_renacimiento', False)
            return {'answer': 'Sí' if es_renacimiento else 'No', 'clarification': ''}
        
        # === VIVIÓ EN LA ANTIGÜEDAD ===
        if 'antiguedad' in pregunta_norm or 'vivio en la antiguedad' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            antiguedad = periodo.get('vivio_antiguedad', False)
            return {'answer': 'Sí' if antiguedad else 'No', 'clarification': ''}
        
        # === MEDIEVO / MEDIEVAL ===
        if 'medievo' in pregunta_norm or 'medieval' in pregunta_norm or 'edad media' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            medieval = periodo.get('es_medieval', False)
            return {'answer': 'Sí' if medieval else 'No', 'clarification': ''}
        
        # === PODERES ===
        if 'poderes' in pregunta_norm or 'superpoderes' in pregunta_norm:
            tiene_poderes = personaje.get('tiene_poderes', False)
            return {'answer': 'Sí' if tiene_poderes else 'No', 'clarification': ''}
        
        # === UNIVERSO - DC ===
        if any(palabra in pregunta_norm for palabra in ['dc comics', 'dc']):
            universo = personaje.get('universo', '').lower()
            return {'answer': 'Sí' if 'dc' in universo else 'No', 'clarification': ''}
        
        # === UNIVERSO - MARVEL ===
        if 'marvel' in pregunta_norm:
            universo = personaje.get('universo', '').lower()
            return {'answer': 'Sí' if 'marvel' in universo else 'No', 'clarification': ''}
        
        # === UNIVERSO - HARRY POTTER ===
        if 'harry potter' in pregunta_norm:
            universo = personaje.get('universo', '').lower()
            return {'answer': 'Sí' if 'harry potter' in universo else 'No', 'clarification': ''}
        
        # === UNIVERSO - STAR WARS ===
        if 'star wars' in pregunta_norm:
            universo = personaje.get('universo', '').lower()
            return {'answer': 'Sí' if 'star wars' in universo else 'No', 'clarification': ''}
        
        # === SEÑOR DE LOS ANILLOS ===
        if 'senor de los anillos' in pregunta_norm or 'el senor de los anillos' in pregunta_norm:
            universo = personaje.get('universo', '')
            return {'answer': 'Sí' if 'tolkien' in universo.lower() else 'No', 'clarification': ''}
        
        # === CARACTERÍSTICAS FÍSICAS ===
        if 'gafas' in pregunta_norm or 'lentes' in pregunta_norm or 'anteojos' in pregunta_norm:
            caracteristicas = personaje.get('caracteristicas', [])
            usa_gafas = any('gafas' in str(c).lower() for c in caracteristicas)
            return {'answer': 'Sí' if usa_gafas else 'No', 'clarification': ''}
        
        # === ARCO ===
        if 'arco' in pregunta_norm:
            armas = personaje.get('armas_objetos', {})
            tiene_arco = armas.get('tiene_arco', False)
            return {'answer': 'Sí' if tiene_arco else 'No', 'clarification': ''}
        
        # === USA ESPADA ===
        if 'espada' in pregunta_norm or 'usa espada' in pregunta_norm:
            armas = personaje.get('armas_objetos', {})
            espada = armas.get('usa_espada', False)
            return {'answer': 'Sí' if espada else 'No', 'clarification': ''}
        
        # === PORTA ARMAS ===
        if 'porta' in pregunta_norm and 'arma' in pregunta_norm:
            armas = personaje.get('armas_objetos', {})
            porta = armas.get('porta_armas', False)
            return {'answer': 'Sí' if porta else 'No', 'clarification': ''}
        
        # === FIGURA ICÓNICA ===
        if 'figura iconica' in pregunta_norm or 'figura iconic' in pregunta_norm or 'icono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            iconico = impacto.get('figura_iconica', False) or impacto.get('iconico', False)
            return {'answer': 'Sí' if iconico else 'No', 'clarification': ''}
        
        # === LIBERAL / CONSERVADOR ===
        if 'liberal' in pregunta_norm:
            ideologia = personaje.get('ideologia', {})
            liberal = ideologia.get('liberal', False)
            return {'answer': 'Sí' if liberal else 'No', 'clarification': ''}
        
        if 'conservador' in pregunta_norm:
            ideologia = personaje.get('ideologia', {})
            conservador = ideologia.get('conservador', False)
            return {'answer': 'Sí' if conservador else 'No', 'clarification': ''}
        
        # === BAJO / ALTO (ESTATURA) ===
        if 'es bajo' in pregunta_norm or 'estatura baja' in pregunta_norm:
            fisico = personaje.get('fisico', {})
            bajo = fisico.get('bajo', False)
            return {'answer': 'Sí' if bajo else 'No', 'clarification': ''}
        
        if 'es alto' in pregunta_norm or 'estatura alta' in pregunta_norm:
            fisico = personaje.get('fisico', {})
            alto = fisico.get('alto', False)
            return {'answer': 'Sí' if alto else 'No', 'clarification': ''}
        
        # === INMORTAL ===
        if 'inmortal' in pregunta_norm or 'vivir para siempre' in pregunta_norm:
            habilidades = personaje.get('habilidades', {})
            inmortal = habilidades.get('es_inmortal', False)
            return {'answer': 'Sí' if inmortal else 'No', 'clarification': ''}
        
        # === LUCHÓ POR LA LIBERTAD ===
        if 'lucho' in pregunta_norm and 'libertad' in pregunta_norm:
            moral = personaje.get('perfil_moral', {})
            lucho = moral.get('lucho_libertad', False)
            return {'answer': 'Sí' if lucho else 'No', 'clarification': ''}
        
        # === CAMBIÓ EL CURSO DE LA HISTORIA ===
        if 'cambio' in pregunta_norm and 'historia' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            cambio = impacto.get('cambio_historia', False)
            return {'answer': 'Sí' if cambio else 'No', 'clarification': ''}
        
        # === TODO EL MUNDO LO CONOCE ===
        if 'todo el mundo' in pregunta_norm or 'todo mundo' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            conocido = impacto.get('todo_mundo_conoce', False)
            return {'answer': 'Sí' if conocido else 'No', 'clarification': ''}
        
        # === USA TECNOLOGÍA AVANZADA ===
        if 'tecnologia' in pregunta_norm and 'avanzada' in pregunta_norm:
            armas = personaje.get('armas_objetos', {})
            tech = armas.get('usa_tecnologia_avanzada', False)
            return {'answer': 'Sí' if tech else 'No', 'clarification': ''}
        
        # === VUELA ===
        if 'vuela' in pregunta_norm or 'puede volar' in pregunta_norm:
            habilidades = personaje.get('habilidades', {})
            vuela = habilidades.get('vuela', False)
            return {'answer': 'Sí' if vuela else 'No', 'clarification': ''}
        
        # === HABILIDADES ESPECIALES ===
        if 'habilidades especiales' in pregunta_norm:
            habilidades = personaje.get('habilidades', {})
            tiene = habilidades.get('tiene_habilidades_especiales', False)
            return {'answer': 'Sí' if tiene else 'No', 'clarification': ''}
        
        # === FUERZA SOBREHUMANA ===
        if 'fuerza sobrehumana' in pregunta_norm:
            habilidades = personaje.get('habilidades', {})
            fuerza = habilidades.get('fuerza_sobrehumana', False)
            return {'answer': 'Sí' if fuerza else 'No', 'clarification': ''}
        
        # === OCUPÓ CARGO POLÍTICO ===
        if 'cargo politico' in pregunta_norm or ('ocupo' in pregunta_norm and 'politico' in pregunta_norm):
            rol = personaje.get('rol', {})
            cargo = rol.get('ocupo_cargo_politico', False)
            return {'answer': 'Sí' if cargo else 'No', 'clarification': ''}
        
        # === INVENTOR ===
        if 'inventor' in pregunta_norm:
            rol = personaje.get('rol', {})
            inventor = rol.get('es_inventor', False)
            return {'answer': 'Sí' if inventor else 'No', 'clarification': ''}
        
        # === GADGETS ===
        if 'gadget' in pregunta_norm:
            armas = personaje.get('armas_objetos', {})
            gadgets = armas.get('tiene_gadgets', False)
            return {'answer': 'Sí' if gadgets else 'No', 'clarification': ''}
        
        # === HIZO DESCUBRIMIENTOS ===
        if 'descubrimiento' in pregunta_norm or 'hizo descubrimientos' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            descubrio = impacto.get('hizo_descubrimientos', False)
            return {'answer': 'Sí' if descubrio else 'No', 'clarification': ''}
        
        # === PERSONAJE MALVADO / ANTAGONISTA ===
        if 'malvado' in pregunta_norm or 'villano' in pregunta_norm:
            rol = personaje.get('rol', {})
            antagonista = rol.get('antagonista', False)
            return {'answer': 'Sí' if antagonista else 'No', 'clarification': ''}
        
        # === ESCONDE SU IDENTIDAD ===
        if 'esconde' in pregunta_norm and 'identidad' in pregunta_norm:
            caracteristicas = personaje.get('caracteristicas', [])
            esconde = any('mascara' in str(c).lower() or 'armadura' in str(c).lower() for c in caracteristicas)
            return {'answer': 'Sí' if esconde else 'No', 'clarification': ''}
        
        # === DRAMATURGO / AUTOR DE OBRAS ===
        if 'dramaturgo' in pregunta_norm:
            profesion = personaje.get('profesion', '').lower()
            area = personaje.get('area', '').lower()
            es_dramaturgo = 'escritor' in profesion and 'literatura' in area
            return {'answer': 'Sí' if es_dramaturgo else 'No', 'clarification': ''}
        
        if 'autor de obras' in pregunta_norm:
            profesion = personaje.get('profesion', '').lower()
            return {'answer': 'Sí' if 'escritor' in profesion else 'No', 'clarification': ''}
        
        # === MONARCA / REY / REINA ===
        if 'monarca' in pregunta_norm or 'rey' in pregunta_norm or 'reina' in pregunta_norm:
            profesion = personaje.get('profesion', '').lower()
            return {'answer': 'Sí' if 'rey' in profesion or 'reina' in profesion else 'No', 'clarification': ''}
        
        # === PRESIDENTE ===
        if 'presidente' in pregunta_norm:
            caracteristicas = personaje.get('caracteristicas', [])
            es_presidente = any('presidente' in str(c).lower() for c in caracteristicas)
            return {'answer': 'Sí' if es_presidente else 'No', 'clarification': ''}
        
        # === ESCULTOR ===
        if 'escultor' in pregunta_norm:
            profesion = personaje.get('profesion', '').lower()
            return {'answer': 'Sí' if 'escultor' in profesion else 'No', 'clarification': ''}
        
        # === PELO FACIAL / BARBA ===
        if 'pelo facial' in pregunta_norm or 'barba' in pregunta_norm or 'barbudo' in pregunta_norm:
            caracteristicas = personaje.get('caracteristicas', [])
            tiene_barba = any('barba' in str(c).lower() or 'bigote' in str(c).lower() for c in caracteristicas)
            return {'answer': 'Sí' if tiene_barba else 'No', 'clarification': ''}
        
        # === OTRO PLANETA / EXTRATERRESTRE ===
        if 'otro planeta' in pregunta_norm or 'extraterrestre' in pregunta_norm:
            nacionalidad = personaje.get('nacionalidad', '').lower()
            es_espacial = 'espacial' in nacionalidad or 'tierra media' in nacionalidad
            return {'answer': 'Sí' if es_espacial else 'No', 'clarification': ''}
        
        # === LÍDER ===
        if 'lider' in pregunta_norm:
            rol = personaje.get('rol', {})
            lider = rol.get('lider', False)
            return {'answer': 'Sí' if lider else 'No', 'clarification': ''}
        
        # === GOBERNANTE ===
        if 'gobernante' in pregunta_norm or 'goberno' in pregunta_norm:
            rol = personaje.get('rol', {})
            gobernante = rol.get('gobernante', False)
            return {'answer': 'Sí' if gobernante else 'No', 'clarification': ''}
        
        # === GENERAL ===
        if 'general' in pregunta_norm and 'estadisticas' not in pregunta_norm:
            rol = personaje.get('rol', {})
            general = rol.get('general', False)
            return {'answer': 'Sí' if general else 'No', 'clarification': ''}
        
        # === REVOLUCIONÓ SU CAMPO ===
        if 'revolucion' in pregunta_norm or 'revoluciono' in pregunta_norm:
            impacto = personaje.get('impacto', {})
            revoluciono = impacto.get('revoluciono_campo', False)
            return {'answer': 'Sí' if revoluciono else 'No', 'clarification': ''}
        
        # === PREMIOS / PREMIO NOBEL ===
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
        
        # === ANTES DE CRISTO ===
        if 'antes de cristo' in pregunta_norm or 'antes cristo' in pregunta_norm:
            periodo = personaje.get('periodo', {})
            antes_cristo = periodo.get('antes_de_cristo', False)
            return {'answer': 'Sí' if antes_cristo else 'No', 'clarification': ''}
        
        # === PACIFISTA ===
        if 'pacifista' in pregunta_norm or 'paz' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            pacifista = perfil.get('pacifista', False)
            return {'answer': 'Sí' if pacifista else 'No', 'clarification': ''}
        
        # === VIOLENTO ===
        if 'violento' in pregunta_norm or 'violencia' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            violento = perfil.get('violento', False)
            return {'answer': 'Sí' if violento else 'No', 'clarification': ''}
        
        # === CONQUISTADOR ===
        if 'conquistador' in pregunta_norm or 'conquisto' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            conquistador = perfil.get('conquistador', False)
            return {'answer': 'Sí' if conquistador else 'No', 'clarification': ''}
        
        # === IMPERIALISTA ===
        if 'imperialista' in pregunta_norm or 'imperio' in pregunta_norm:
            perfil = personaje.get('perfil_moral', {})
            imperialista = perfil.get('imperialista', False)
            return {'answer': 'Sí' if imperialista else 'No', 'clarification': ''}
        
        # === HÉROE ===
        if 'heroe' in pregunta_norm:
            rol = personaje.get('rol', {})
            heroe = rol.get('heroe', False)
            return {'answer': 'Sí' if heroe else 'No', 'clarification': ''}
        
        # === ANTAGONISTA ===
        if 'antagonista' in pregunta_norm:
            rol = personaje.get('rol', {})
            antagonista = rol.get('antagonista', False)
            return {'answer': 'Sí' if antagonista else 'No', 'clarification': ''}
        
        # NO CLASIFICABLE - Registrar como hueco
        RegistroHuecos.registrar(pregunta, pregunta_norm, personaje.get('nombre', 'Desconocido'))
        
        return {
            'answer': 'No lo sé',
            'clarification': 'Esa pregunta no está en mi base de conocimiento. Intenta preguntar de otra forma.'
        }


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
        
        # Huecos
        output.write("ANÁLISIS DE HUECOS\n")
        output.write("-" * 80 + "\n")
        output.write(f"Total de Huecos: {len(huecos)}\n\n")
        
        # Preguntas más frecuentes
        preguntas_counter = Counter([h['pregunta_normalizada'] for h in huecos])
        output.write("Top 30 Preguntas Más Frecuentes (Sin Respuesta):\n")
        output.write("-" * 80 + "\n")
        
        for i, (pregunta, cantidad) in enumerate(preguntas_counter.most_common(30), 1):
            output.write(f"{i:2d}. [{cantidad:3d}x] {pregunta}\n")
        output.write("\n")
        
        # Footer
        output.write("=" * 80 + "\n")
        output.write("FIN DEL REPORTE\n")
        output.write("=" * 80 + "\n")
        
        return output.getvalue()


# ===================================================================
# ENDPOINTS API
# ===================================================================

@app.route('/api/oracle', methods=['POST'])
def oracle_endpoint():
    """Endpoint principal del juego"""
    try:
        data = request.json
        action = data.get('action')
        
        if action == 'start':
            # Iniciar nueva partida
            personaje = random.choice(PERSONAJES)
            return jsonify({
                'character': personaje,
                'max_questions': MAX_PREGUNTAS
            })
        
        elif action == 'ask':
            # Responder pregunta
            pregunta = data.get('question', '')
            personaje = data.get('character', {})
            
            analizador = AnalizadorPreguntas()
            respuesta = analizador.analizar(pregunta, personaje)
            
            # Registrar métrica
            metricas_manager.metricas['preguntas_totales'] += 1
            metricas_manager.guardar_metricas()
            
            return jsonify(respuesta)
        
        elif action == 'guess':
            # Verificar adivinanza
            guess = data.get('guess', '').lower().strip()
            personaje = data.get('character', {})
            nombre_real = personaje.get('nombre', '').lower().strip()
            
            correcto = guess == nombre_real
            
            # Registrar partida
            metricas_manager.registrar_partida(
                personaje.get('nombre', 'Desconocido'),
                correcto,
                data.get('questions_used', 0)
            )
            
            return jsonify({
                'correct': correcto,
                'character': personaje.get('nombre')
            })
        
        return jsonify({'error': 'Acción inválida'}), 400
    
    except Exception as e:
        metricas_manager.registrar_error(str(e), f"Action: {data.get('action', 'unknown')}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'personajes': len(PERSONAJES),
        'mensaje': 'The Oracle está funcionando correctamente'
    })


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


@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Retorna estadísticas para el dashboard"""
    try:
        stats = {
            'partidas_totales': metricas_manager.metricas.get('partidas_totales', 0),
            'partidas_ganadas': metricas_manager.metricas.get('partidas_ganadas', 0),
            'preguntas_totales': metricas_manager.metricas.get('preguntas_totales', 0),
            'personajes_usados': metricas_manager.metricas.get('personajes_usados', {}),
            'tasa_exito_por_personaje': metricas_manager.metricas.get('tasa_exito_por_personaje', {})
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/huecos', methods=['GET'])
def dashboard_huecos():
    """Retorna huecos registrados"""
    try:
        huecos = []
        if os.path.exists(REGISTRO_HUECOS_FILE):
            with open(REGISTRO_HUECOS_FILE, 'r', encoding='utf-8') as f:
                huecos = json.load(f)
        return jsonify({'huecos': huecos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/dashboard')
def dashboard():
    """Renderiza el dashboard web"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>The Oracle - Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff00;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            padding: 20px;
            border: 2px solid #00ff00;
            margin-bottom: 30px;
            background: rgba(0, 255, 0, 0.05);
        }
        
        h1 {
            font-size: 2.5em;
            color: #ff00ff;
            text-shadow: 0 0 10px #ff00ff;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #00ff00;
            font-size: 1.2em;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .tab {
            padding: 15px 30px;
            background: rgba(0, 255, 0, 0.1);
            border: 2px solid #00ff00;
            cursor: pointer;
            transition: all 0.3s;
            flex: 1;
            min-width: 150px;
            text-align: center;
        }
        
        .tab:hover, .tab.active {
            background: rgba(255, 0, 255, 0.2);
            border-color: #ff00ff;
            color: #ff00ff;
        }
        
        .tab-content {
            display: none;
            animation: fadeIn 0.3s;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .card {
            background: rgba(0, 255, 0, 0.05);
            border: 2px solid #00ff00;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .card h2 {
            color: #ff00ff;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: rgba(255, 0, 255, 0.1);
            border: 2px solid #ff00ff;
            padding: 20px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2.5em;
            color: #00ff00;
            margin: 10px 0;
            text-shadow: 0 0 10px #00ff00;
        }
        
        .stat-label {
            color: #ff00ff;
            font-size: 0.9em;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            border: 1px solid #00ff00;
            text-align: left;
        }
        
        th {
            background: rgba(255, 0, 255, 0.2);
            color: #ff00ff;
        }
        
        tr:hover {
            background: rgba(0, 255, 0, 0.1);
        }
        
        .list-item {
            padding: 10px;
            border-bottom: 1px solid #00ff00;
            display: flex;
            justify-content: space-between;
        }
        
        .refresh-button {
            background: rgba(0, 255, 0, 0.2);
            border: 2px solid #00ff00;
            color: #00ff00;
            padding: 12px 24px;
            cursor: pointer;
            font-family: inherit;
            font-size: 1em;
            transition: all 0.3s;
        }
        
        .refresh-button:hover {
            background: rgba(255, 0, 255, 0.3);
            border-color: #ff00ff;
            color: #ff00ff;
        }
        
        .error {
            color: #ff0000;
            border-color: #ff0000;
        }
        
        @media (max-width: 768px) {
            .stat-grid {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 1.8em;
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
            <div class="tab active" onclick="switchTab('general')">📊 General</div>
            <div class="tab" onclick="switchTab('huecos')">🕳️ Huecos</div>
        </div>
        
        <div id="general" class="tab-content active">
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-label">Partidas Totales</div>
                    <div class="stat-value" id="partidas-totales">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Partidas Ganadas</div>
                    <div class="stat-value" id="partidas-ganadas">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Tasa Victoria</div>
                    <div class="stat-value" id="tasa-victoria">0%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Preguntas Totales</div>
                    <div class="stat-value" id="preguntas-totales">0</div>
                </div>
            </div>
            
            <div class="card">
                <h2>Top 10 Personajes Más Jugados</h2>
                <div id="top-personajes"></div>
            </div>
        </div>
        
        <div id="huecos" class="tab-content">
            <div class="card">
                <h2>Análisis de Huecos</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total de Huecos</div>
                        <div class="stat-value" id="total-huecos">0</div>
                    </div>
                </div>
                
                <h2 style="margin-top: 20px;">Top 20 Preguntas Más Frecuentes</h2>
                <div id="preguntas-frecuentes"></div>
                
                <h2 style="margin-top: 20px;">Últimos 30 Huecos</h2>
                <div id="ultimos-huecos"></div>
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {
            // Ocultar todos los contenidos
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Desactivar todas las tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Activar tab seleccionada
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/dashboard/stats');
                const data = await response.json();
                
                document.getElementById('partidas-totales').textContent = data.partidas_totales || 0;
                document.getElementById('partidas-ganadas').textContent = data.partidas_ganadas || 0;
                document.getElementById('preguntas-totales').textContent = data.preguntas_totales || 0;
                
                const tasa = data.partidas_totales > 0 
                    ? ((data.partidas_ganadas / data.partidas_totales) * 100).toFixed(2)
                    : 0;
                document.getElementById('tasa-victoria').textContent = tasa + '%';
                
                // Top personajes
                const personajes = Object.entries(data.personajes_usados || {})
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 10);
                
                const topHtml = personajes.map(([nombre, veces], i) => 
                    `<div class="list-item">
                        <span>${i + 1}. ${nombre}</span>
                        <span>${veces} veces</span>
                    </div>`
                ).join('');
                
                document.getElementById('top-personajes').innerHTML = topHtml || '<p>No hay datos</p>';
            } catch (error) {
                console.error('Error cargando stats:', error);
            }
        }
        
        async function loadHuecos() {
            try {
                const response = await fetch('/api/dashboard/huecos');
                const data = await response.json();
                const huecos = data.huecos || [];
                
                document.getElementById('total-huecos').textContent = huecos.length;
                
                // Contar preguntas frecuentes
                const counter = {};
                huecos.forEach(h => {
                    const p = h.pregunta_normalizada;
                    counter[p] = (counter[p] || 0) + 1;
                });
                
                const sorted = Object.entries(counter)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 20);
                
                const frecuentesHtml = sorted.map(([pregunta, veces], i) =>
                    `<div class="list-item">
                        <span>${i + 1}. ${pregunta}</span>
                        <span>${veces}x</span>
                    </div>`
                ).join('');
                
                document.getElementById('preguntas-frecuentes').innerHTML = 
                    frecuentesHtml || '<p>No hay huecos registrados</p>';
                
                // Últimos huecos
                const ultimos = huecos.slice(-30).reverse();
                const ultimosHtml = ultimos.map(h =>
                    `<div class="list-item">
                        <span>${h.personaje}: ${h.pregunta_original}</span>
                        <span>${h.timestamp.substring(0, 19)}</span>
                    </div>`
                ).join('');
                
                document.getElementById('ultimos-huecos').innerHTML = 
                    ultimosHtml || '<p>No hay huecos registrados</p>';
            } catch (error) {
                console.error('Error cargando huecos:', error);
            }
        }
        
        function loadAllData() {
            loadStats();
            loadHuecos();
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
    """
    return render_template_string(html)


# ===================================================================
# MAIN
# ===================================================================

if __name__ == '__main__':
    print("="*60)
    print("🧠 THE ORACLE - Backend con Dashboard")
    print("="*60)
    print(f"📡 Servidor: http://0.0.0.0:5000")
    print(f"🎭 Personajes: {len(PERSONAJES)}")
    print(f"📊 Dashboard: http://0.0.0.0:5000/dashboard")
    print("="*60)
    
    # Puerto para producción
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
