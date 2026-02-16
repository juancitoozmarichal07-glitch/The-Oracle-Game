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
        return {'answer': 'Sí' if personaje['genero'] == 'hombre' else 'No', 'clarification': ''}
    
    if any(kw in pregunta_procesada for kw in ['mujer', 'chica', 'ella', 'femenino', 'dama']):
        return {'answer': 'Sí' if personaje['genero'] == 'mujer' else 'No', 'clarification': ''}
    
    # === VIVO/MUERTO ===
    if any(kw in pregunta_procesada for kw in ['vivo', 'vive', 'sigue vivo', 'esta vivo', 'actualmente', 'presente']):
        return {'answer': 'Sí' if personaje.get('vivo', False) else 'No', 'clarification': ''}
    
    if any(kw in pregunta_procesada for kw in ['muerto', 'murio', 'fallecio', 'difunto']):
        return {'answer': 'Sí' if not personaje.get('vivo', False) else 'No', 'clarification': ''}
    
    # === FAMOSO ===
    if any(kw in pregunta_procesada for kw in ['famoso', 'conocido', 'celebre', 'popular', 'renombrado']):
        return {'answer': 'Sí' if personaje.get('famoso', False) else 'No', 'clarification': ''}
    
    # === RICO ===
    if any(kw in pregunta_procesada for kw in ['rico', 'millonario', 'dinero', 'fortuna', 'adinerado']):
        return {'answer': 'Sí' if personaje.get('rico', False) else 'No', 'clarification': ''}
    
    if 'pobre' in pregunta_procesada:
        return {'answer': 'No' if personaje.get('rico', False) else 'Sí', 'clarification': ''}
    
    # === PROFESIÓN: CIENTÍFICO ===
    if any(kw in pregunta_procesada for kw in ['cientifico', 'ciencia', 'cientifica', 'investigador', 'laboratorio']):
        es_cientifico = personaje.get('profesion') in ['cientifico', 'cientifica'] or personaje.get('area') in ['fisica', 'quimica']
        return {'answer': 'Sí' if es_cientifico else 'No', 'clarification': ''}
    
    # === PROFESIÓN: ARTISTA ===
    if any(kw in pregunta_procesada for kw in ['artista', 'pintor', 'pintora', 'arte', 'cuadro', 'lienzo', 'pintura']):
        es_artista = personaje.get('profesion') in ['artista'] or personaje.get('area') in ['pintura', 'arte']
        return {'answer': 'Sí' if es_artista else 'No', 'clarification': ''}
    
    # === PROFESIÓN: ESCRITOR ===
    if any(kw in pregunta_procesada for kw in ['escritor', 'escritora', 'autor', 'autora', 'literatura', 'libro', 'novela', 'poeta']):
        es_escritor = personaje.get('profesion') in ['escritor'] or personaje.get('area') in ['literatura']
        return {'answer': 'Sí' if es_escritor else 'No', 'clarification': ''}
    
    # === PROFESIÓN: MILITAR/GUERRERO ===
    if any(kw in pregunta_procesada for kw in ['militar', 'soldado', 'guerrero', 'guerrera', 'guerra', 'combate', 'batalla']):
        es_militar = personaje.get('profesion') in ['militar', 'guerrera', 'guerrero'] or personaje.get('area') in ['guerra', 'militar', 'combate']
        return {'answer': 'Sí' if es_militar else 'No', 'clarification': ''}
    
    # === MAGIA ===
    if any(kw in pregunta_procesada for kw in ['mago', 'magia', 'magico', 'bruja', 'brujo', 'hechicero', 'hechicera', 'varita']):
        es_mago = personaje.get('profesion') in ['mago', 'bruja'] or personaje.get('area') == 'magia' or personaje.get('poder') == 'magico'
        return {'answer': 'Sí' if es_mago else 'No', 'clarification': ''}
    
    # === SUPERHÉROE ===
    if any(kw in pregunta_procesada for kw in ['superheroe', 'superheroina', 'super heroe', 'capa', 'poderes especiales']):
        es_superheroe = personaje.get('profesion') in ['superheroe'] or personaje.get('poder') in ['sobrehumano', 'aracnido', 'tecnologico']
        return {'answer': 'Sí' if es_superheroe else 'No', 'clarification': ''}
    
    # === VILLANO ===
    if any(kw in pregunta_procesada for kw in ['villano', 'malo', 'malvado', 'antagonista']):
        return {'answer': 'Sí' if personaje.get('profesion') == 'villano' else 'No', 'clarification': ''}
    
    # === PODER SOBREHUMANO ===
    if any(kw in pregunta_procesada for kw in ['poderoso', 'sobrehumano', 'superpoderes', 'habilidad especial', 'superfuerza', 'poderes']):
        tiene_poder = personaje.get('poder') in ['sobrehumano', 'magico', 'la fuerza', 'aracnido', 'tecnologico']
        return {'answer': 'Sí' if tiene_poder else 'No', 'clarification': ''}
    
    # === NACIONALIDAD: EUROPA ===
    if any(kw in pregunta_procesada for kw in ['europeo', 'europa', 'del viejo continente']):
        es_europeo = personaje.get('nacionalidad') in ['aleman', 'frances', 'francesa', 'ingles', 'inglesa', 'italiano', 'espanol', 'espanola', 'polaca']
        return {'answer': 'Sí' if es_europeo else 'No', 'clarification': ''}
    
    # === NACIONALIDAD: AMÉRICA ===
    if any(kw in pregunta_procesada for kw in ['americano', 'america', 'estados unidos', 'eeuu']):
        es_americano = personaje.get('nacionalidad') in ['estadounidense', 'mexicana', 'mexicano']
        return {'answer': 'Sí' if es_americano else 'No', 'clarification': ''}
    
    # === ÉPOCA: ANTIGUA ===
    if any(kw in pregunta_procesada for kw in ['antiguo', 'antigua', 'edad antigua', 'epoca antigua']):
        return {'answer': 'Sí' if personaje.get('epoca_antigua', False) else 'No', 'clarification': ''}
    
    # === ÉPOCA: MEDIEVAL ===
    if any(kw in pregunta_procesada for kw in ['medieval', 'edad media', 'medioevo']):
        return {'answer': 'Sí' if personaje.get('edad_media', False) else 'No', 'clarification': ''}
    
    # === ANTES DEL AÑO 1500 ===
    if any(kw in pregunta_procesada for kw in ['antes de 1500', 'antes del año 1500', 'anterior a 1500']):
        return {'answer': 'Sí' if personaje.get('antes_1500', False) else 'No', 'clarification': ''}
    
    # === MODERNO ===
    if any(kw in pregunta_procesada for kw in ['moderno', 'moderna', 'contemporaneo', 'siglo xx', 'siglo 20', 'siglo xxi', 'siglo 21']):
        return {'answer': 'Sí' if personaje.get('epoca') == 'moderna' else 'No', 'clarification': ''}
    
    # === CARACTERÍSTICAS FÍSICAS ===
    if any(kw in pregunta_procesada for kw in ['gafas', 'lentes', 'anteojos']):
        tiene_gafas = any('gafas' in str(c).lower() for c in personaje.get('caracteristicas', []))
        return {'answer': 'Sí' if tiene_gafas else 'No', 'clarification': ''}
    
    if any(kw in pregunta_procesada for kw in ['barba', 'barbudo']):
        tiene_barba = any('barba' in str(c).lower() for c in personaje.get('caracteristicas', []))
        return {'answer': 'Sí' if tiene_barba else 'No', 'clarification': ''}
    
    # === UNIVERSO: HARRY POTTER ===
    if any(kw in pregunta_procesada for kw in ['harry potter', 'hogwarts']):
        return {'answer': 'Sí' if personaje.get('universo') == 'Harry Potter' else 'No', 'clarification': ''}
    
    # === UNIVERSO: DC COMICS ===
    if any(kw in pregunta_procesada for kw in ['dc comics', 'dc']):
        return {'answer': 'Sí' if personaje.get('universo') == 'DC Comics' else 'No', 'clarification': ''}
    
    # === UNIVERSO: MARVEL ===
    if any(kw in pregunta_procesada for kw in ['marvel', 'vengadores']):
        return {'answer': 'Sí' if personaje.get('universo') == 'Marvel' else 'No', 'clarification': ''}
    
    # === ES HUMANO? (AHORA VA AL FINAL, DESPUÉS DE TODOS LOS CHEQUEOS ESPECÍFICOS) ===
    if any(kw in pregunta_procesada for kw in ['humano', 'ser humano', 'es humano', 'humana', 'persona humana']):
        # Personajes reales son humanos
        if personaje['tipo'] == 'real':
            return {'answer': 'Sí', 'clarification': ''}
        # Personajes ficticios con casos especiales (no humanos)
        elif personaje['nombre'] in ['Gandalf', 'Darth Vader', 'Wonder Woman']:
            return {'answer': 'No', 'clarification': ''}
        # El resto de ficticios (Sherlock, Harry, etc.) son humanos
        else:
            return {'answer': 'Sí', 'clarification': ''}
    
    # === RESPUESTA POR DEFECTO (pregunta válida pero no reconocida) ===
    return {
        'answer': 'No lo sé',
        'clarification': 'No estoy seguro de cómo interpretar eso. ¿Podrías reformularlo?'
    }


# ===================================================================
# SISTEMA DE SUGERENCIAS MEJORADO
# ===================================================================

def generar_sugerencias(personaje, question_count, asked_questions):
    """
    Genera sugerencias INTELIGENTES basadas en:
    - Lo que ya se preguntó
    - El género del personaje
    - Si es real o ficticio
    - Evita preguntas absurdas
    """
    
    # Normalizar preguntas ya hechas para comparación
    preguntas_normalizadas = [normalizar_texto(q) for q in asked_questions]
    
    # Determinar qué información ya tenemos
    info_conocida = {
        'tipo': any('real' in q or 'ficticio' in q for q in preguntas_normalizadas),
        'genero': any('hombre' in q or 'mujer' in q for q in preguntas_normalizadas),
        'vivo': any('vivo' in q or 'muerto' in q for q in preguntas_normalizadas),
        'famoso': any('famoso' in q for q in preguntas_normalizadas),
        'rico': any('rico' in q or 'pobre' in q for q in preguntas_normalizadas),
        'epoca': any('antigu' in q or 'medieval' in q or 'modern' in q or '1500' in q for q in preguntas_normalizadas),
        'profesion': any('cientific' in q or 'artista' in q or 'escritor' in q or 'militar' in q or 'guerrer' in q or 'mago' in q for q in preguntas_normalizadas),
        'poder': any('poder' in q or 'superpoder' in q for q in preguntas_normalizadas),
        'nacionalidad': any('europe' in q or 'americ' in q for q in preguntas_normalizadas),
        'universo': any('harry potter' in q or 'dc' in q or 'marvel' in q for q in preguntas_normalizadas),
        'caracteristicas': any('gafas' in q or 'barba' in q for q in preguntas_normalizadas),
    }
    
    # Saber el género del personaje (si ya lo descubrimos)
    genero_descubierto = None
    if info_conocida['genero']:
        for q in asked_questions:
            q_norm = normalizar_texto(q)
            if 'hombre' in q_norm or 'varon' in q_norm or 'masculino' in q_norm:
                genero_descubierto = 'hombre'
                break
            elif 'mujer' in q_norm or 'femenino' in q_norm or 'dama' in q_norm:
                genero_descubierto = 'mujer'
                break
    
    # Base de preguntas posibles con condiciones lógicas
    todas_preguntas = [
        # === CATEGORÍA TIPO ===
        {"texto": "¿Es una persona real?", "categoria": "tipo", 
         "condicion": not info_conocida['tipo']},
        
        # === CATEGORÍA GÉNERO ===
        {"texto": "¿Es hombre?", "categoria": "genero", 
         "condicion": not info_conocida['genero']},
        {"texto": "¿Es mujer?", "categoria": "genero", 
         "condicion": not info_conocida['genero']},
        
        # === CATEGORÍA VIVO/MUERTO ===
        {"texto": "¿Está vivo actualmente?", "categoria": "vivo", 
         "condicion": not info_conocida['vivo']},
        
        # === CATEGORÍA NACIONALIDAD ===
        {"texto": "¿Es de Europa?", "categoria": "nacionalidad", 
         "condicion": not info_conocida['nacionalidad'] and personaje['tipo'] == 'real'},
        {"texto": "¿Es de América?", "categoria": "nacionalidad", 
         "condicion": not info_conocida['nacionalidad'] and personaje['tipo'] == 'real'},
        
        # === CATEGORÍA ÉPOCA ===
        {"texto": "¿Es de época antigua?", "categoria": "epoca", 
         "condicion": not info_conocida['epoca'] and personaje['tipo'] == 'real'},
        {"texto": "¿Vivió en la Edad Media?", "categoria": "epoca", 
         "condicion": not info_conocida['epoca'] and personaje['tipo'] == 'real'},
        {"texto": "¿Es de época moderna?", "categoria": "epoca", 
         "condicion": not info_conocida['epoca'] and personaje['tipo'] == 'real'},
        
        # === CATEGORÍA PROFESIÓN ===
        {"texto": "¿Es científico?", "categoria": "profesion", 
         "condicion": not info_conocida['profesion'] and personaje['tipo'] == 'real'},
        {"texto": "¿Es artista?", "categoria": "profesion", 
         "condicion": not info_conocida['profesion'] and personaje['tipo'] == 'real'},
        {"texto": "¿Es escritor?", "categoria": "profesion", 
         "condicion": not info_conocida['profesion'] and personaje['tipo'] == 'real'},
        {"texto": "¿Es militar o guerrero?", "categoria": "profesion", 
         "condicion": not info_conocida['profesion'] and personaje['tipo'] == 'real'},
        {"texto": "¿Es mago o brujo?", "categoria": "profesion", 
         "condicion": not info_conocida['profesion'] and personaje['tipo'] == 'ficticio'},
        {"texto": "¿Es superhéroe?", "categoria": "profesion", 
         "condicion": not info_conocida['profesion'] and personaje['tipo'] == 'ficticio'},
        {"texto": "¿Es villano?", "categoria": "profesion", 
         "condicion": not info_conocida['profesion'] and personaje['tipo'] == 'ficticio'},
        
        # === CATEGORÍA PODERES ===
        {"texto": "¿Tiene poderes sobrehumanos?", "categoria": "poder", 
         "condicion": not info_conocida['poder'] and personaje['tipo'] == 'ficticio'},
        
        # === CATEGORÍA UNIVERSO ===
        {"texto": "¿Pertenece al universo de Harry Potter?", "categoria": "universo", 
         "condicion": not info_conocida['universo'] and personaje['tipo'] == 'ficticio'},
        {"texto": "¿Pertenece a DC Comics?", "categoria": "universo", 
         "condicion": not info_conocida['universo'] and personaje['tipo'] == 'ficticio'},
        {"texto": "¿Pertenece a Marvel?", "categoria": "universo", 
         "condicion": not info_conocida['universo'] and personaje['tipo'] == 'ficticio'},
        
        # === CATEGORÍA FAMA Y RIQUEZA ===
        {"texto": "¿Es famoso?", "categoria": "famoso", 
         "condicion": not info_conocida['famoso']},
        {"texto": "¿Es rico o millonario?", "categoria": "rico", 
         "condicion": not info_conocida['rico']},
        
        # === CATEGORÍA CARACTERÍSTICAS FÍSICAS ===
        {"texto": "¿Usa gafas?", "categoria": "caracteristicas", 
         "condicion": not info_conocida['caracteristicas']},
    ]
    
    # Añadir pregunta de barba solo si no sabemos que es mujer
    if not info_conocida['caracteristicas']:
        if genero_descubierto != 'mujer':
            todas_preguntas.append({
                "texto": "¿Tiene barba?",
                "categoria": "caracteristicas",
                "condicion": True
            })
    
    # Filtrar preguntas que ya se hicieron
    sugerencias_disponibles = []
    for pregunta in todas_preguntas:
        if not pregunta["condicion"]:
            continue
            
        pregunta_normalizada = normalizar_texto(pregunta["texto"])
        ya_preguntada = False
        
        for q_hecha in preguntas_normalizadas:
            palabras_preg = set(pregunta_normalizada.split())
            palabras_hecha = set(q_hecha.split())
            
            if len(palabras_preg & palabras_hecha) >= 2:
                ya_preguntada = True
                break
        
        if not ya_preguntada:
            sugerencias_disponibles.append(pregunta["texto"])
    
    # Si no hay suficientes, añadir preguntas genéricas
    if len(sugerencias_disponibles) < 3:
        preguntas_genericas = [
            "¿Es conocido mundialmente?",
            "¿Murió de forma trágica?",
            "¿Aparece en películas o libros?"
        ]
        
        for pg in preguntas_genericas:
            pg_norm = normalizar_texto(pg)
            ya_preguntada = any(
                len(set(pg_norm.split()) & set(q.split())) >= 2 
                for q in preguntas_normalizadas
            )
            
            if not ya_preguntada and pg not in sugerencias_disponibles:
                sugerencias_disponibles.append(pg)
    
    # Asegurar entre 3 y 5 sugerencias
    num_sugerencias = min(5, len(sugerencias_disponibles))
    num_sugerencias = max(3, num_sugerencias)
    
    if len(sugerencias_disponibles) > num_sugerencias:
        return random.sample(sugerencias_disponibles, num_sugerencias)
    else:
        return sugerencias_disponibles


# ===================================================================
# SISTEMA DE PISTAS
# ===================================================================

def generar_pista(personaje, nivel):
    """
    Genera pistas enigmáticas (máximo 2 por personaje)
    """
    pistas = personaje.get('pistas_enigmaticas', [])
    
    if nivel == 1 and len(pistas) > 0:
        return pistas[0]
    elif nivel == 2 and len(pistas) > 1:
        return pistas[1]
    else:
        return "No hay más pistas disponibles."


# ===================================================================
# ENDPOINTS DE LA API
# ===================================================================

@app.route('/api/oracle', methods=['POST'])
def oracle():
    """Endpoint principal del juego"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'start':
            character = random.choice(PERSONAJES)
            return jsonify({
                'character': character,
                'message': 'Juego iniciado'
            })
        
        elif action == 'ask':
            question = data.get('question', '')
            character = data.get('character', {})
            
            if not question.strip():
                return jsonify({
                    'answer': 'No lo sé',
                    'clarification': 'No escuché ninguna pregunta.'
                })
            
            response = analizar_pregunta(question, character)
            return jsonify(response)
        
        elif action == 'guess':
            guess = data.get('guess', '').lower().strip()
            character = data.get('character', {})
            character_name = character.get('nombre', '').lower().strip()
            
            # Normalizar ambos para comparación robusta
            guess_norm = normalizar_texto(guess)
            name_norm = normalizar_texto(character_name)
            
            # Verificar similitud
            correct = guess_norm == name_norm
            
            # Si no es exacto, probar similitud
            if not correct and len(guess_norm) > 3:
                ratio = difflib.SequenceMatcher(None, guess_norm, name_norm).ratio()
                correct = ratio > 0.85
            
            return jsonify({
                'correct': correct,
                'character': character['nombre']
            })
        
        elif action == 'suggestions':
            character = data.get('character', {})
            question_count = data.get('question_count', 0)
            asked_questions = data.get('asked_questions', [])
            
            suggestions = generar_sugerencias(character, question_count, asked_questions)
            return jsonify({'suggestions': suggestions})
        
        elif action == 'hint':
            character = data.get('character', {})
            hint_level = data.get('hint_level', 1)
            
            hint = generar_pista(character, hint_level)
            return jsonify({'hint': hint})
        
        else:
            return jsonify({'error': 'Acción no válida'}), 400
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud"""
    return jsonify({
        'status': 'ok',
        'personajes': len(PERSONAJES),
        'mensaje': '🧠 The Oracle - 20 Personajes'
    })


@app.route('/', methods=['GET'])
def home():
    """Página de inicio"""
    return """
    <html>
    <head><title>The Oracle</title></head>
    <body style="font-family:sans-serif; background:#000; color:#0f0; padding:20px; text-align:center;">
        <h1 style="color:#ff00ff;">🧠 THE ORACLE</h1>
        <p>20 Personajes Disponibles</p>
        <p>Sistema Mejorado con Normalización y Sinónimos</p>
        <p>✅ VERSIÓN CORREGIDA - Sugerencias Inteligentes</p>
    </body>
    </html>
    """


# ===================================================================
# EJECUCIÓN DEL SERVIDOR
# ===================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🧠 THE ORACLE - Backend Mejorado VERSIÓN CORREGIDA")
    print("=" * 60)
    print(f"📡 Servidor: http://0.0.0.0:5000")
    print(f"🎭 Personajes: {len(PERSONAJES)}")
    print("✅ Normalización de texto activada")
    print("✅ Sistema de sinónimos mejorado")
    print("✅ Validación flexible de preguntas")
    print("✅ Sugerencias inteligentes basadas en contexto")
    print("✅ Comparación de nombres con similitud")
    print("✅ Campos de época corregidos para Juana de Arco")
    print("✅ Filtro de género para preguntas físicas")
    print("✅ Pregunta '¿Es humano?' agregada (Sí/No seco)")
    print("=" * 60)
    
    # Para producción con Gunicorn
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
