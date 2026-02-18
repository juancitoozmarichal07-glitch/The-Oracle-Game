#!/usr/bin/env python3
"""
THE ORACLE - Backend CORREGIDO
Versión: 20 personajes + Sistema FUNCIONAL
- ✅ Clasificación de preguntas ARREGLADA
- ✅ Respuestas CORRECTAS
- ✅ Sugerencias ÚTILES
- ✅ Sistema simplificado pero COMPLETO
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
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
MAX_PREGUNTAS = 20


# ===================================================================
# BASE DE DATOS - 20 PERSONAJES
# ===================================================================

PERSONAJES = [
    # REALES (10)
    {
        "nombre": "Albert Einstein",
        "tipo": "real",
        "genero": "masculino",
        "nacionalidad": "aleman",
        "profesion": "cientifico",
        "area": "fisica",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "caracteristicas": ["gafas", "bigote", "genio"],
        "pistas": [
            "El tiempo fluye diferente en su universo teórico",
            "E=mc² es solo el comienzo de su legado"
        ]
    },
    {
        "nombre": "Cleopatra",
        "tipo": "real",
        "genero": "femenino",
        "nacionalidad": "egipcia",
        "profesion": "reina",
        "area": "politica",
        "epoca": "antigua",
        "vivo": False,
        "famoso": True,
        "rico": True,
        "caracteristicas": ["bella", "seductora", "faraona"],
        "pistas": [
            "El veneno de una serpiente selló su destino",
            "César y Marco Antonio cayeron ante su encanto"
        ]
    },
    {
        "nombre": "Leonardo da Vinci",
        "tipo": "real",
        "genero": "masculino",
        "nacionalidad": "italiano",
        "profesion": "artista",
        "area": "arte",
        "epoca": "renacimiento",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "caracteristicas": ["pintor", "inventor", "genio"],
        "pistas": [
            "Una sonrisa enigmática vigila siglos desde su lienzo",
            "Dibujó máquinas voladoras antes de que existieran"
        ]
    },
    {
        "nombre": "Marie Curie",
        "tipo": "real",
        "genero": "femenino",
        "nacionalidad": "polaca",
        "profesion": "cientifica",
        "area": "quimica",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "caracteristicas": ["radiactividad", "nobel", "pionera"],
        "pistas": [
            "Tocó elementos que brillaban con luz mortal",
            "Dos Premios Nobel no detuvieron su pasión"
        ]
    },
    {
        "nombre": "Napoleon Bonaparte",
        "tipo": "real",
        "genero": "masculino",
        "nacionalidad": "frances",
        "profesion": "militar",
        "area": "guerra",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": True,
        "caracteristicas": ["emperador", "estratega", "bajo"],
        "pistas": [
            "Una isla lo vio nacer y otra lo vio morir",
            "El invierno ruso congeló sus sueños de imperio"
        ]
    },
    {
        "nombre": "Frida Kahlo",
        "tipo": "real",
        "genero": "femenino",
        "nacionalidad": "mexicana",
        "profesion": "artista",
        "area": "arte",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "caracteristicas": ["monoceja", "autorretratos", "flores"],
        "pistas": [
            "Su espejo fue testigo del dolor transformado en arte",
            "Flores coronan su cabeza mientras el sufrimiento habita"
        ]
    },
    {
        "nombre": "William Shakespeare",
        "tipo": "real",
        "genero": "masculino",
        "nacionalidad": "ingles",
        "profesion": "escritor",
        "area": "literatura",
        "epoca": "renacimiento",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "caracteristicas": ["dramaturgo", "poeta", "hamlet"],
        "pistas": [
            "Ser o no ser, esa pregunta eterna nació de su genio",
            "Los amantes de Verona murieron por su pluma"
        ]
    },
    {
        "nombre": "Gandhi",
        "tipo": "real",
        "genero": "masculino",
        "nacionalidad": "indio",
        "profesion": "lider",
        "area": "politica",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "caracteristicas": ["pacifista", "gafas", "asceta"],
        "pistas": [
            "Caminó al mar por un puñado de sal prohibida",
            "Sin disparar un arma liberó a millones"
        ]
    },
    {
        "nombre": "Juana de Arco",
        "tipo": "real",
        "genero": "femenino",
        "nacionalidad": "francesa",
        "profesion": "guerrera",
        "area": "guerra",
        "epoca": "medieval",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "caracteristicas": ["santa", "armadura", "visionaria"],
        "pistas": [
            "Voces celestiales la guiaron a vestir armadura",
            "Las llamas la consumieron pero su fe quedó"
        ]
    },
    {
        "nombre": "Pablo Picasso",
        "tipo": "real",
        "genero": "masculino",
        "nacionalidad": "espanol",
        "profesion": "artista",
        "area": "arte",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": True,
        "caracteristicas": ["cubismo", "guernica", "prolifico"],
        "pistas": [
            "Rompió la realidad en mil fragmentos geométricos",
            "El horror de la guerra grita en su lienzo"
        ]
    },
    
    # FICTICIOS (10)
    {
        "nombre": "Harry Potter",
        "tipo": "ficticio",
        "genero": "masculino",
        "nacionalidad": "ingles",
        "profesion": "mago",
        "area": "magia",
        "universo": "Harry Potter",
        "epoca": "moderna",
        "vivo": True,
        "famoso": True,
        "rico": True,
        "tiene_poderes": True,
        "caracteristicas": ["cicatriz", "gafas", "varita"],
        "pistas": [
            "Una cicatriz con forma de rayo marca su frente",
            "El niño que sobrevivió a la maldición más terrible"
        ]
    },
    {
        "nombre": "Sherlock Holmes",
        "tipo": "ficticio",
        "genero": "masculino",
        "nacionalidad": "ingles",
        "profesion": "detective",
        "area": "investigacion",
        "universo": "Literatura",
        "epoca": "victoriana",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "tiene_poderes": False,
        "caracteristicas": ["deductivo", "pipa", "gorra"],
        "pistas": [
            "Desde el 221B de Baker Street desentraña misterios",
            "Elemental, mi querido... aunque nunca dijo eso"
        ]
    },
    {
        "nombre": "Wonder Woman",
        "tipo": "ficticio",
        "genero": "femenino",
        "nacionalidad": "amazona",
        "profesion": "superheroe",
        "area": "combate",
        "universo": "DC",
        "epoca": "moderna",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "tiene_poderes": True,
        "caracteristicas": ["lazo verdad", "amazona", "fuerte"],
        "pistas": [
            "Un lazo dorado obliga a confesar la verdad",
            "Hija de dioses, criada por guerreras"
        ]
    },
    {
        "nombre": "Darth Vader",
        "tipo": "ficticio",
        "genero": "masculino",
        "nacionalidad": "espacial",
        "profesion": "villano",
        "area": "guerra",
        "universo": "Star Wars",
        "epoca": "futuro",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "tiene_poderes": True,
        "caracteristicas": ["armadura negra", "respirador", "sith"],
        "pistas": [
            "Su respiración mecánica anuncia el terror",
            "Cayó en la oscuridad pero un hijo lo redimió"
        ]
    },
    {
        "nombre": "Batman",
        "tipo": "ficticio",
        "genero": "masculino",
        "nacionalidad": "americano",
        "profesion": "superheroe",
        "area": "justicia",
        "universo": "DC",
        "epoca": "moderna",
        "vivo": True,
        "famoso": True,
        "rico": True,
        "tiene_poderes": False,
        "caracteristicas": ["murcielago", "millonario", "gotham"],
        "pistas": [
            "La muerte de sus padres forjó al caballero oscuro",
            "Sin poderes pero con tecnología y miedo"
        ]
    },
    {
        "nombre": "Hermione Granger",
        "tipo": "ficticio",
        "genero": "femenino",
        "nacionalidad": "inglesa",
        "profesion": "bruja",
        "area": "magia",
        "universo": "Harry Potter",
        "epoca": "moderna",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "tiene_poderes": True,
        "caracteristicas": ["inteligente", "estudiosa", "leal"],
        "pistas": [
            "Los libros son su mayor tesoro y arma",
            "Nacida sin magia pero convertida en la más brillante"
        ]
    },
    {
        "nombre": "Spiderman",
        "tipo": "ficticio",
        "genero": "masculino",
        "nacionalidad": "americano",
        "profesion": "superheroe",
        "area": "justicia",
        "universo": "Marvel",
        "epoca": "moderna",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "tiene_poderes": True,
        "caracteristicas": ["telarañas", "mascara", "joven"],
        "pistas": [
            "Una picadura radioactiva le dio poderes",
            "Con gran poder viene gran responsabilidad"
        ]
    },
    {
        "nombre": "Gandalf",
        "tipo": "ficticio",
        "genero": "masculino",
        "nacionalidad": "tierra media",
        "profesion": "mago",
        "area": "magia",
        "universo": "Tolkien",
        "epoca": "medieval",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "tiene_poderes": True,
        "caracteristicas": ["barba blanca", "baston", "sabio"],
        "pistas": [
            "Gris al principio, blanco después de las sombras",
            "Un simple anillo debía ser destruido"
        ]
    },
    {
        "nombre": "Don Quijote",
        "tipo": "ficticio",
        "genero": "masculino",
        "nacionalidad": "espanol",
        "profesion": "caballero",
        "area": "aventuras",
        "universo": "Literatura",
        "epoca": "renacimiento",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "tiene_poderes": False,
        "caracteristicas": ["loco", "molinos", "idealista"],
        "pistas": [
            "Confundió molinos de viento con gigantes",
            "Su locura era más noble que la cordura"
        ]
    },
    {
        "nombre": "Mulan",
        "tipo": "ficticio",
        "genero": "femenino",
        "nacionalidad": "china",
        "profesion": "guerrera",
        "area": "guerra",
        "universo": "Leyenda",
        "epoca": "antigua",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "tiene_poderes": False,
        "caracteristicas": ["valiente", "disfraz", "honor"],
        "pistas": [
            "Cortó su cabello y vistió armadura por su padre",
            "Nadie supo que el soldado era una mujer"
        ]
    }
]


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
            
        print(f"📝 Hueco registrado: '{pregunta}' para {personaje.get('nombre')}")
    except Exception as e:
        print(f"⚠️ Error registrando hueco: {e}")


# ===================================================================
# MEMORIA DE PARTIDA
# ===================================================================

class MemoriaPartida:
    def __init__(self):
        self.preguntas = []
        self.respuestas = []
        self.preguntas_restantes = MAX_PREGUNTAS
    
    def registrar(self, pregunta: str, respuesta: str):
        self.preguntas.append(pregunta)
        self.respuestas.append(respuesta)
        self.preguntas_restantes -= 1
    
    def puede_seguir(self) -> bool:
        return self.preguntas_restantes > 0


memorias = {}


# ===================================================================
# ENDPOINTS
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
            memorias[session_id] = MemoriaPartida()
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
                memorias[session_id] = MemoriaPartida()
            
            memoria = memorias[session_id]
            
            if not memoria.puede_seguir():
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'personajes': len(PERSONAJES),
        'mensaje': '🧠 The Oracle - Sistema CORREGIDO'
    })


@app.route('/', methods=['GET'])
def home():
    return """
    <html>
    <head><title>The Oracle</title></head>
    <body style="font-family:sans-serif; background:#000; color:#0f0; padding:20px; text-align:center;">
        <h1 style="color:#ff00ff;">🧠 THE ORACLE</h1>
        <p>20 Personajes | Sistema CORREGIDO</p>
        <p>✅ Respuestas FUNCIONAN</p>
        <p>✅ Sugerencias ÚTILES</p>
        <p>✅ Todo SIMPLIFICADO y FUNCIONAL</p>
    </body>
    </html>
    """


if __name__ == '__main__':
    import os
    print("=" * 60)
    print("🧠 THE ORACLE - Backend CORREGIDO")
    print("=" * 60)
    print(f"📡 Servidor: http://0.0.0.0:5000")
    print(f"🎭 Personajes: {len(PERSONAJES)}")
    print("✅ Sistema SIMPLIFICADO")
    print("✅ Respuestas FUNCIONAN")
    print("✅ Sugerencias ÚTILES")
    print("=" * 60)
    
    # Puerto para producción
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
