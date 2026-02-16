#!/usr/bin/env python3
"""
THE ORACLE - Backend Mejorado y Pulido VERSIÓN FINAL
Compatible con Pydroid (Android) y frontend game.js
20 Personajes + Sistema Robusto de Respuestas
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import unicodedata
import difflib

app = Flask(__name__)
CORS(app)


# ===================================================================
# SISTEMA DE NORMALIZACIÓN Y SINÓNIMOS
# ===================================================================

def normalizar_texto(texto):
    """
    Normaliza el texto para hacerlo más fácil de procesar:
    - Convierte a minúsculas
    - Elimina tildes y acentos
    - Quita signos de puntuación
    - Elimina espacios extra
    """
    if not texto:
        return ""
    
    # Convertir a minúsculas
    texto = texto.lower()
    
    # Eliminar tildes usando NFD (Normalization Form Decomposition)
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(char for char in texto if unicodedata.category(char) != 'Mn')
    
    # Eliminar signos de puntuación comunes
    signos = '¿?¡!.,;:()[]{}"\'-'
    for signo in signos:
        texto = texto.replace(signo, ' ')
    
    # Eliminar espacios extra
    texto = ' '.join(texto.split())
    
    return texto


# Diccionario de sinónimos mejorado
SINONIMOS = {
    # Profesiones y roles
    'superheroina': 'superheroe',
    'hechicera': 'mago',
    'hechicero': 'mago',
    'maga': 'mago',
    'bruja': 'mago',
    'brujo': 'mago',
    'cientifico': 'cientifico',
    'cientifica': 'cientifico',
    'escritora': 'escritor',
    'autora': 'escritor',
    'pintora': 'artista',
    'pintor': 'artista',
    'guerrera': 'guerrero',
    
    # Estados
    'muerto': 'muerto',
    'muerta': 'muerto',
    'fallecido': 'muerto',
    'fallecida': 'muerto',
    'difunto': 'muerto',
    'difunta': 'muerto',
    
    # Características
    'adinerado': 'rico',
    'millonario': 'rico',
    'acaudalado': 'rico',
    'pudiente': 'rico',
    
    # Género
    'varon': 'hombre',
    'masculino': 'hombre',
    'chico': 'hombre',
    'tipo': 'hombre',
    'femenino': 'mujer',
    'chica': 'mujer',
    'femina': 'mujer',
    'dama': 'mujer',
    
    # Épocas
    'edad media': 'medieval',
    'medioevo': 'medieval',
    'antigua': 'antiguo',
    'antiguo': 'antiguo',
    'clasico': 'antiguo',
    'clasica': 'antiguo',
    
    # Otros
    'lentes': 'gafas',
    'anteojos': 'gafas',
    'espejuelos': 'gafas',
    'barbudo': 'barba',
    'conocido': 'famoso',
    'celebre': 'famoso',
    'renombrado': 'famoso',
}


def aplicar_sinonimos(texto):
    """
    Reemplaza palabras por sus sinónimos base.
    Procesa palabra por palabra para evitar reemplazos parciales incorrectos.
    """
    palabras = texto.split()
    palabras_procesadas = []
    
    for palabra in palabras:
        # Si la palabra está en el diccionario de sinónimos, usar su versión base
        if palabra in SINONIMOS:
            palabras_procesadas.append(SINONIMOS[palabra])
        else:
            palabras_procesadas.append(palabra)
    
    return ' '.join(palabras_procesadas)


# ===================================================================
# BASE DE DATOS DE 20 PERSONAJES (CORREGIDA)
# ===================================================================

PERSONAJES = [
    # === PERSONAJES REALES (10) ===
    {
        "nombre": "Albert Einstein",
        "tipo": "real",
        "genero": "hombre",
        "nacionalidad": "aleman",
        "profesion": "cientifico",
        "area": "fisica",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "poder": "intelectual",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["genio", "cabello blanco", "bigote", "fisica teorica", "relatividad", "nobel"],
        "pistas_enigmaticas": [
            "El tiempo fluye diferente en su universo teorico",
            "E=mc² es solo el comienzo de su legado inmortal"
        ]
    },
    {
        "nombre": "Cleopatra",
        "tipo": "real",
        "genero": "mujer",
        "nacionalidad": "egipcia",
        "profesion": "reina",
        "area": "politica",
        "epoca": "antigua",
        "vivo": False,
        "famoso": True,
        "rico": True,
        "poder": "politico",
        "edad_media": False,
        "antes_1500": True,
        "epoca_antigua": True,
        "caracteristicas": ["bella", "seductora", "faraona", "egipto", "antigua", "serpiente"],
        "pistas_enigmaticas": [
            "El veneno de una serpiente sello su destino junto al Nilo",
            "Cesar y Marco Antonio cayeron ante su encanto mortal"
        ]
    },
    {
        "nombre": "Leonardo da Vinci",
        "tipo": "real",
        "genero": "hombre",
        "nacionalidad": "italiano",
        "profesion": "artista",
        "area": "arte",
        "epoca": "renacimiento",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "poder": "intelectual",
        "edad_media": False,
        "antes_1500": True,
        "epoca_antigua": False,
        "caracteristicas": ["pintor", "inventor", "genio", "mona lisa", "polimata", "helicoptero"],
        "pistas_enigmaticas": [
            "Una sonrisa enigmática vigila siglos desde su lienzo",
            "Dibujo maquinas voladoras antes de que el cielo las conociera"
        ]
    },
    {
        "nombre": "Marie Curie",
        "tipo": "real",
        "genero": "mujer",
        "nacionalidad": "polaca",
        "profesion": "cientifica",
        "area": "quimica",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "poder": "intelectual",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["radiactividad", "nobel", "pionera", "mujer cientifica", "polonio", "radio"],
        "pistas_enigmaticas": [
            "Toco elementos que brillaban en la oscuridad con luz mortal",
            "Dos Premios Nobel no fueron suficientes para detener su pasion"
        ]
    },
    {
        "nombre": "Napoleon Bonaparte",
        "tipo": "real",
        "genero": "hombre",
        "nacionalidad": "frances",
        "profesion": "militar",
        "area": "guerra",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": True,
        "poder": "militar",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["emperador", "estratega", "bajo", "frances", "conquistas", "waterloo"],
        "pistas_enigmaticas": [
            "Una isla lo vio nacer y otra isla lo vio morir en exilio",
            "El invierno ruso congelo sus sueños de imperio europeo"
        ]
    },
    {
        "nombre": "Frida Kahlo",
        "tipo": "real",
        "genero": "mujer",
        "nacionalidad": "mexicana",
        "profesion": "artista",
        "area": "pintura",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "poder": "artistico",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["monoceja", "autorretratos", "mexicana", "surrealista", "flores", "dolor"],
        "pistas_enigmaticas": [
            "Su espejo fue testigo del dolor transformado en arte salvaje",
            "Flores coronan su cabeza mientras el sufrimiento habita su lienzo"
        ]
    },
    {
        "nombre": "William Shakespeare",
        "tipo": "real",
        "genero": "hombre",
        "nacionalidad": "ingles",
        "profesion": "escritor",
        "area": "literatura",
        "epoca": "renacimiento",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "poder": "intelectual",
        "edad_media": False,
        "antes_1500": True,
        "epoca_antigua": False,
        "caracteristicas": ["dramaturgo", "romeo y julieta", "hamlet", "teatro", "poeta", "macbeth"],
        "pistas_enigmaticas": [
            "Ser o no ser, esa pregunta eterna nacio de su genio",
            "Los amantes de Verona murieron por palabras de su pluma"
        ]
    },
    {
        "nombre": "Gandhi",
        "tipo": "real",
        "genero": "hombre",
        "nacionalidad": "indio",
        "profesion": "lider",
        "area": "politica",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "poder": "moral",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["pacifista", "india", "no violencia", "asceta", "gafas", "sal"],
        "pistas_enigmaticas": [
            "Camino hasta el mar para tomar un puñado de sal prohibida",
            "Sin disparar un arma libero a millones del yugo imperial"
        ]
    },
    {
        "nombre": "Juana de Arco",
        "tipo": "real",
        "genero": "mujer",
        "nacionalidad": "francesa",
        "profesion": "guerrera",
        "area": "militar",
        "epoca": "medieval",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "poder": "militar",
        "edad_media": True,
        "antes_1500": True,
        "epoca_antigua": False,
        "caracteristicas": ["santa", "armadura", "francia", "visionaria", "joven", "hoguera"],
        "pistas_enigmaticas": [
            "Voces celestiales la guiaron a vestir armadura de hombre",
            "Las llamas la consumieron pero su fe quedo inmortalizada"
        ]
    },
    {
        "nombre": "Pablo Picasso",
        "tipo": "real",
        "genero": "hombre",
        "nacionalidad": "espanol",
        "profesion": "artista",
        "area": "pintura",
        "epoca": "moderna",
        "vivo": False,
        "famoso": True,
        "rico": True,
        "poder": "artistico",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["cubismo", "guernica", "espanol", "prolifico", "fragmentado", "azul"],
        "pistas_enigmaticas": [
            "Rompió la realidad en mil fragmentos geométricos de color",
            "El horror de la guerra grita eternamente en su lienzo más célebre"
        ]
    },
    
    # === PERSONAJES FICTICIOS (10) ===
    {
        "nombre": "Harry Potter",
        "tipo": "ficticio",
        "genero": "hombre",
        "nacionalidad": "ingles",
        "profesion": "mago",
        "area": "magia",
        "universo": "Harry Potter",
        "autor": "J.K. Rowling",
        "vivo": True,
        "famoso": True,
        "rico": True,
        "poder": "magico",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["cicatriz", "gafas", "varita", "hogwarts", "huerfano", "relampago"],
        "pistas_enigmaticas": [
            "Una cicatriz con forma de rayo marca su frente y su destino",
            "El niño que sobrevivio a la maldicion mas terrible conocida"
        ]
    },
    {
        "nombre": "Sherlock Holmes",
        "tipo": "ficticio",
        "genero": "hombre",
        "nacionalidad": "ingles",
        "profesion": "detective",
        "area": "investigacion",
        "universo": "Literatura",
        "autor": "Arthur Conan Doyle",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "poder": "intelectual",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["deductivo", "pipa", "gorra", "londres", "brillante", "221b"],
        "pistas_enigmaticas": [
            "Desde el 221B de Baker Street desentraña los misterios londinenses",
            "Elemental, mi querido... aunque nunca dijo esas palabras exactas"
        ]
    },
    {
        "nombre": "Wonder Woman",
        "tipo": "ficticio",
        "genero": "mujer",
        "nacionalidad": "amazona",
        "profesion": "superheroe",
        "area": "combate",
        "universo": "DC Comics",
        "autor": "DC Comics",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "poder": "sobrehumano",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": True,
        "caracteristicas": ["lazo de la verdad", "amazona", "fuerte", "guerrera", "inmortal", "diosa"],
        "pistas_enigmaticas": [
            "Un lazo dorado obliga a confesar la verdad más oculta",
            "Hija de dioses, criada por guerreras en una isla perdida"
        ]
    },
    {
        "nombre": "Darth Vader",
        "tipo": "ficticio",
        "genero": "hombre",
        "nacionalidad": "espacial",
        "profesion": "villano",
        "area": "guerra",
        "universo": "Star Wars",
        "autor": "George Lucas",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "poder": "la fuerza",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["armadura negra", "respirador", "sith", "padre", "caido", "lado oscuro"],
        "pistas_enigmaticas": [
            "Su respiración mecánica anuncia la presencia del terror galáctico",
            "Cayo en la oscuridad pero un hijo lo redimio al final"
        ]
    },
    {
        "nombre": "Batman",
        "tipo": "ficticio",
        "genero": "hombre",
        "nacionalidad": "estadounidense",
        "profesion": "superheroe",
        "area": "justicia",
        "universo": "DC Comics",
        "autor": "DC Comics",
        "vivo": True,
        "famoso": True,
        "rico": True,
        "poder": "tecnologico",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["murcielago", "millonario", "gotham", "huerfano", "sin poderes", "oscuro"],
        "pistas_enigmaticas": [
            "La muerte de sus padres forjó al caballero de la noche eterna",
            "Sin poderes pero con tecnologia y miedo como sus armas"
        ]
    },
    {
        "nombre": "Hermione Granger",
        "tipo": "ficticio",
        "genero": "mujer",
        "nacionalidad": "inglesa",
        "profesion": "bruja",
        "area": "magia",
        "universo": "Harry Potter",
        "autor": "J.K. Rowling",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "poder": "magico",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["inteligente", "cabello rizado", "estudiosa", "leal", "varita", "libros"],
        "pistas_enigmaticas": [
            "Los libros son su mayor tesoro y su arma más poderosa",
            "Nacida sin magia pero convertida en la bruja más brillante"
        ]
    },
    {
        "nombre": "Spiderman",
        "tipo": "ficticio",
        "genero": "hombre",
        "nacionalidad": "estadounidense",
        "profesion": "superheroe",
        "area": "justicia",
        "universo": "Marvel",
        "autor": "Marvel Comics",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "poder": "aracnido",
        "edad_media": False,
        "antes_1500": False,
        "epoca_antigua": False,
        "caracteristicas": ["telarañas", "mascara", "joven", "trepa paredes", "peter parker", "araña"],
        "pistas_enigmaticas": [
            "Una picadura radioactiva le dio lo que la ciencia no pudo",
            "Con gran poder viene una responsabilidad aun mayor"
        ]
    },
    {
        "nombre": "Gandalf",
        "tipo": "ficticio",
        "genero": "hombre",
        "nacionalidad": "tierra media",
        "profesion": "mago",
        "area": "magia",
        "universo": "El Señor de los Anillos",
        "autor": "J.R.R. Tolkien",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "poder": "magico",
        "edad_media": True,
        "antes_1500": True,
        "epoca_antigua": False,
        "caracteristicas": ["barba blanca", "baston", "sabio", "anciano", "sombrero", "anillo"],
        "pistas_enigmaticas": [
            "Gris al principio, blanco después de vencer a las sombras",
            "Un simple anillo debía ser destruido para salvar el mundo"
        ]
    },
    {
        "nombre": "Don Quijote",
        "tipo": "ficticio",
        "genero": "hombre",
        "nacionalidad": "espanol",
        "profesion": "caballero",
        "area": "aventuras",
        "universo": "Literatura",
        "autor": "Miguel de Cervantes",
        "vivo": False,
        "famoso": True,
        "rico": False,
        "poder": "ninguno",
        "edad_media": True,
        "antes_1500": True,
        "epoca_antigua": False,
        "caracteristicas": ["loco", "molinos", "rocinante", "idealista", "armadura vieja", "dulcinea"],
        "pistas_enigmaticas": [
            "Confundió molinos de viento con gigantes temibles",
            "Su locura era más noble que la cordura de muchos"
        ]
    },
    {
        "nombre": "Mulan",
        "tipo": "ficticio",
        "genero": "mujer",
        "nacionalidad": "china",
        "profesion": "guerrera",
        "area": "militar",
        "universo": "Leyenda china",
        "autor": "Leyenda",
        "vivo": True,
        "famoso": True,
        "rico": False,
        "poder": "militar",
        "edad_media": True,
        "antes_1500": True,
        "epoca_antigua": True,
        "caracteristicas": ["valiente", "disfraz", "china", "honor", "espada", "hombre"],
        "pistas_enigmaticas": [
            "Cortó su cabello y vistió armadura para salvar a su padre",
            "Durante años nadie supo que el soldado era una mujer"
        ]
    }
]


# ===================================================================
# SISTEMA DE ANÁLISIS DE PREGUNTAS MEJORADO
# ===================================================================

def es_pregunta_valida(pregunta):
    """
    Verifica si la pregunta tiene contenido mínimo.
    """
    pregunta = pregunta.strip()
    
    # Muy corta (menos de 3 caracteres)
    if len(pregunta) < 3:
        return False
    
    # Si tiene al menos 2 palabras, probablemente es válida
    palabras = pregunta.split()
    if len(palabras) >= 2:
        return True
    
    # Si es una sola palabra, verificar si es pregunta común
    palabra_unica = palabras[0].lower()
    preguntas_validas_una_palabra = ['real', 'ficticio', 'hombre', 'mujer', 'vivo', 'muerto', 
                                      'famoso', 'rico', 'pobre', 'antiguo', 'moderno', 'medieval']
    if palabra_unica in preguntas_validas_una_palabra:
        return True
    
    return False


def analizar_pregunta(pregunta, personaje):
    """
    Analiza pregunta y devuelve respuesta robusta.
    """
    # PASO 1: Normalizar el texto
    pregunta_normalizada = normalizar_texto(pregunta)
    
    # PASO 2: Aplicar sinónimos
    pregunta_procesada = aplicar_sinonimos(pregunta_normalizada)
    
    # Verificar validez básica
    if not es_pregunta_valida(pregunta_procesada):
        return {
            'answer': 'No lo sé',
            'clarification': 'No estoy seguro de cómo interpretar eso. ¿Podrías reformularlo?'
        }
    
    # === TIPO: REAL O FICTICIO ===
    if any(kw in pregunta_procesada for kw in ['real', 'existio', 'verdad', 'historico', 'vivio en realidad', 'persona real']):
        return {'answer': 'Sí' if personaje['tipo'] == 'real' else 'No', 'clarification': ''}
    
    if any(kw in pregunta_procesada for kw in ['ficticio', 'inventado', 'imaginario', 'ficcion', 'cuento', 'historia inventada']):
        return {'answer': 'Sí' if personaje['tipo'] == 'ficticio' else 'No', 'clarification': ''}
    
    # === GÉNERO ===
    if any(kw in pregunta_procesada for kw in ['hombre', 'varon', 'masculino', 'el', 'tipo']):
        return {'answer': 'Sí' if personaje['genero'] == 'hombre' else 'No', 'clarification
