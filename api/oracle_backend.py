#!/usr/bin/env python3
"""
THE ORACLE - Backend Definitivo COMPLETO
=========================================
Versión: 30 personajes + Razonamiento Estratégico + Sugerencias Inteligentes

Incluye:
- ✅ 30 personajes con estructura completa
- ✅ Normalización + Sinónimos
- ✅ Clasificador de preguntas
- ✅ Motor de respuestas (Sí/No/Probablemente)
- ✅ Registro de huecos
- ✅ Memoria de partida (coherencia)
- ✅ Orientación por 5 negativos
- ✅ Razonamiento estratégico para sugerencias
- ✅ Endpoints completos
- ✅ 100% determinista, sin IA
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import random
import unicodedata
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from difflib import SequenceMatcher
from enum import Enum
from dataclasses import dataclass, field

app = Flask(__name__)
CORS(app)


# ===================================================================
# CONFIGURACIÓN GLOBAL
# ===================================================================

REGISTRO_HUECOS_FILE = "huecos_diccionario.json"
MAX_PREGUNTAS = 20
UMBRAL_SIMILITUD = 0.85
NO_CONSECUTIVOS_ORIENTACION = 5


# ===================================================================
# MODELO ESTRUCTURADO DE PERSONAJE
# ===================================================================

class Personaje:
    """Estructura fija para todos los personajes"""
    
    CAMPOS_OBLIGATORIOS = [
        "id", "nombre", "tipo", "genero", "siglo", "epoca", 
        "nacionalidad", "area_principal", "subareas", "universo", 
        "rasgos_booleanos", "matices", "pistas"
    ]
    
    RASGOS_PREDEFINIDOS = [
        "tiene_poderes", "es_historico", "es_cientifico", "es_artista", 
        "es_escritor", "es_militar", "es_lider", "es_religioso", 
        "es_heroe", "es_villano", "usa_tecnologia", "tiene_identidad_secreta",
        "es_multimillonario", "es_famoso", "es_animal", "es_divino",
        "tiene_barba", "usa_gafas", "usa_capa", "usa_mascara", "usa_armadura",
        "puede_volar", "es_inmortal", "es_detective", "premios_nobel",
        "es_mago", "es_reina", "es_emperador", "es_faraon", "es_filosofo",
        "es_explorador", "es_inventor", "es_compositor", "es_astronauta",
        "es_presidente", "es_cientifico_nuclear", "es_biologo", "es_fisico",
        "es_quimico", "es_matematico", "es_poeta", "es_dramaturgo",
        "es_pintor", "es_escultor", "es_arquitecto", "es_musico",
        "es_actor", "es_director", "es_cantante", "es_deportista",
        "es_heroe_mitologico", "es_dios", "es_semidios", "es_titan",
        "es_gigante", "es_monstruo"
    ]


# ===================================================================
# BASE DE DATOS - 30 PERSONAJES (COMPLETA)
# ===================================================================

PERSONAJES = [
    # === 1. WONDER WOMAN ===
    {
        "id": "wonder_woman",
        "nombre": "Wonder Woman",
        "tipo": "ficticio",
        "genero": "femenino",
        "siglo": "XX",
        "epoca": "contemporaneo",
        "nacionalidad": "amazona",
        "area_principal": "ficcion",
        "subareas": ["superheroes", "mitologia"],
        "universo": "DC",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": True,
            "es_lider": True, "es_religioso": False, "es_heroe": True,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": True,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": True, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": True,
            "puede_volar": True, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": True,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": True,
            "es_dios": False, "es_semidios": True, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_humana": {"respuesta_matiz": "Probablemente no", "aclaracion": "Su origen es divino, aunque vive entre mortales"},
            "tiene_poderes_sobrehumanos": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Sus dones vienen de los dioses, no de la genética"}
        },
        "pistas": [
            "Un lazo dorado obliga a confesar la verdad más oculta",
            "Hija de dioses, criada por guerreras en una isla perdida"
        ]
    },
    
    # === 2. BATMAN ===
    {
        "id": "batman",
        "nombre": "Batman",
        "tipo": "ficticio",
        "genero": "masculino",
        "siglo": "XX",
        "epoca": "contemporaneo",
        "nacionalidad": "estadounidense",
        "area_principal": "ficcion",
        "subareas": ["superheroes"],
        "universo": "DC",
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": True, "es_religioso": False, "es_heroe": True,
            "es_villano": False, "usa_tecnologia": True, "tiene_identidad_secreta": True,
            "es_multimillonario": True, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": True, "usa_mascara": True, "usa_armadura": True,
            "puede_volar": False, "es_inmortal": False, "es_detective": True,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": True, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "tiene_poderes_sobrehumanos": {"respuesta_matiz": "Probablemente no", "aclaracion": "Su grandeza viene del entrenamiento, no de la genética"},
            "es_inmortal": {"respuesta_matiz": "Probablemente no", "aclaracion": "Su leyenda es eterna, pero su cuerpo no"}
        },
        "pistas": [
            "Opera principalmente de noche",
            "Su símbolo representa un animal nocturno"
        ]
    },
    
    # === 3. GANDALF ===
    {
        "id": "gandalf",
        "nombre": "Gandalf",
        "tipo": "ficticio",
        "genero": "masculino",
        "siglo": "Edad Media",
        "epoca": "medieval",
        "nacionalidad": "valinor",
        "area_principal": "ficcion",
        "subareas": ["fantasia", "literatura"],
        "universo": "Tolkien",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": True, "es_religioso": False, "es_heroe": True,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": True, "tiene_barba": True, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": True, "es_detective": False,
            "premios_nobel": False, "es_mago": True, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": True,
            "es_explorador": True, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": True,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_humano": {"respuesta_matiz": "Probablemente no", "aclaracion": "Su forma es mortal, su espíritu es eterno"},
            "es_anciano": {"respuesta_matiz": "Probablemente no", "aclaracion": "Su apariencia es anciana, pero su ser es atemporal"}
        },
        "pistas": [
            "Gris al principio, blanco después de vencer a las sombras",
            "Un simple anillo debía ser destruido para salvar el mundo"
        ]
    },
    
    # === 4. SHERLOCK HOLMES ===
    {
        "id": "sherlock_holmes",
        "nombre": "Sherlock Holmes",
        "tipo": "ficticio",
        "genero": "masculino",
        "siglo": "XIX",
        "epoca": "victoriano",
        "nacionalidad": "ingles",
        "area_principal": "ficcion",
        "subareas": ["literatura", "misterio"],
        "universo": "Literatura",
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": True,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": True,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": True, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_real": {"respuesta_matiz": "Probablemente no", "aclaracion": "Inspirado en un cirujano, pero su casa es de papel"}
        },
        "pistas": [
            "Desde el 221B de Baker Street desentraña los misterios londinenses",
            "Elemental, mi querido... aunque nunca dijo esas palabras exactas"
        ]
    },
    
    # === 5. HARRY POTTER ===
    {
        "id": "harry_potter",
        "nombre": "Harry Potter",
        "tipo": "ficticio",
        "genero": "masculino",
        "siglo": "XX",
        "epoca": "contemporaneo",
        "nacionalidad": "ingles",
        "area_principal": "ficcion",
        "subareas": ["fantasia", "literatura", "cine"],
        "universo": "Harry Potter",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": True, "es_religioso": False, "es_heroe": True,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": True,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": True, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": True, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": True, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_mortal": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Puede morir, pero el amor lo protege"}
        },
        "pistas": [
            "Una cicatriz con forma de rayo marca su frente y su destino",
            "El niño que sobrevivió a la maldición más terrible conocida"
        ]
    },
    
    # === 6. MARIE CURIE ===
    {
        "id": "marie_curie",
        "nombre": "Marie Curie",
        "tipo": "real",
        "genero": "femenino",
        "siglo": "XIX-XX",
        "epoca": "contemporaneo",
        "nacionalidad": "polaca",
        "area_principal": "ciencia",
        "subareas": ["quimica", "fisica"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": True,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": True, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": True, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": True,
            "es_biologo": False, "es_fisico": True, "es_quimico": True,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_lider": {"respuesta_matiz": "Probablemente no", "aclaracion": "Su liderazgo fue científico, no político"}
        },
        "pistas": [
            "Tocó elementos que brillaban en la oscuridad con luz mortal",
            "Dos Premios Nobel no fueron suficientes para detener su pasión"
        ]
    },
    
    # === 7. LEONARDO DA VINCI ===
    {
        "id": "leonardo_da_vinci",
        "nombre": "Leonardo da Vinci",
        "tipo": "real",
        "genero": "masculino",
        "siglo": "XV-XVI",
        "epoca": "renacimiento",
        "nacionalidad": "italiano",
        "area_principal": "arte",
        "subareas": ["pintura", "inventos", "ciencia"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": True,
            "es_artista": True, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": True, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": True, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": True,
            "es_explorador": False, "es_inventor": True, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": True, "es_fisico": True, "es_quimico": True,
            "es_matematico": True, "es_poeta": True, "es_dramaturgo": False,
            "es_pintor": True, "es_escultor": True, "es_arquitecto": True,
            "es_musico": True, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_cientifico": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Su ciencia era arte, y su arte era ciencia"}
        },
        "pistas": [
            "Una sonrisa enigmática vigila siglos desde su lienzo",
            "Dibujó máquinas voladoras antes de que el cielo las conociera"
        ]
    },
    
    # === 8. ALBERT EINSTEIN ===
    {
        "id": "albert_einstein",
        "nombre": "Albert Einstein",
        "tipo": "real",
        "genero": "masculino",
        "siglo": "XX",
        "epoca": "contemporaneo",
        "nacionalidad": "alemana",
        "area_principal": "ciencia",
        "subareas": ["fisica", "matematicas"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": True,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": True, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": True, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": True, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": True,
            "es_explorador": False, "es_inventor": False, "es_compositor": True,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": True,
            "es_biologo": False, "es_fisico": True, "es_quimico": False,
            "es_matematico": True, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": True, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_inventor": {"respuesta_matiz": "Probablemente no", "aclaracion": "Fue un teórico, no un inventor de artefactos"},
            "es_musico": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Tocaba el violín y la música inspiraba su ciencia"}
        },
        "pistas": [
            "El tiempo fluye diferente en su universo teórico",
            "E=mc² es solo el comienzo de su legado inmortal"
        ]
    },
    
    # === 9. CLEOPATRA ===
    {
        "id": "cleopatra",
        "nombre": "Cleopatra",
        "tipo": "real",
        "genero": "femenino",
        "siglo": "I a.C.",
        "epoca": "antigua",
        "nacionalidad": "egipcia",
        "area_principal": "politica",
        "subareas": ["realeza", "historia"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": True, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": True, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": True,
            "es_emperador": False, "es_faraon": True, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_egipcia_nativa": {"respuesta_matiz": "Probablemente no", "aclaracion": "Era griega por ascendencia, pero faraona de Egipto"}
        },
        "pistas": [
            "El veneno de una serpiente selló su destino junto al Nilo",
            "César y Marco Antonio cayeron ante su encanto mortal"
        ]
    },
    
    # === 10. NAPOLEÓN BONAPARTE ===
    {
        "id": "napoleon",
        "nombre": "Napoleón Bonaparte",
        "tipo": "real",
        "genero": "masculino",
        "siglo": "XVIII-XIX",
        "epoca": "moderna",
        "nacionalidad": "francesa",
        "area_principal": "politica",
        "subareas": ["militar", "historia"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": True,
            "es_lider": True, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": True, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_bajo": {"respuesta_matiz": "Probablemente sí", "aclaracion": "La leyenda dice que era bajo, pero era de estatura promedio para su época"}
        },
        "pistas": [
            "Una isla lo vio nacer y otra isla lo vio morir en exilio",
            "El invierno ruso congeló sus sueños de imperio europeo"
        ]
    },
    
    # === 11. FRIDA KAHLO ===
    {
        "id": "frida_kahlo",
        "nombre": "Frida Kahlo",
        "tipo": "real",
        "genero": "femenino",
        "siglo": "XX",
        "epoca": "contemporaneo",
        "nacionalidad": "mexicana",
        "area_principal": "arte",
        "subareas": ["pintura", "cultura"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": False,
            "es_artista": True, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": True, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_surrealista": {"respuesta_matiz": "Probablemente no", "aclaracion": "Ella decía: 'Nunca pinté sueños, pinté mi propia realidad'"}
        },
        "pistas": [
            "Su espejo fue testigo del dolor transformado en arte salvaje",
            "Flores coronan su cabeza mientras el sufrimiento habita su lienzo"
        ]
    },
    
    # === 12. WILLIAM SHAKESPEARE ===
    {
        "id": "shakespeare",
        "nombre": "William Shakespeare",
        "tipo": "real",
        "genero": "masculino",
        "siglo": "XVI-XVII",
        "epoca": "renacimiento",
        "nacionalidad": "inglesa",
        "area_principal": "literatura",
        "subareas": ["teatro", "poesia"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": False,
            "es_artista": True, "es_escritor": True, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": True, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": True,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": True, "es_dramaturgo": True,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": True, "es_director": True,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_un_hombre": {"respuesta_matiz": "Probablemente sí", "aclaracion": "La mayoría de académicos cree que fue un hombre, aunque hay teorías"}
        },
        "pistas": [
            "Ser o no ser, esa pregunta eterna nació de su genio",
            "Los amantes de Verona murieron por palabras de su pluma"
        ]
    },
    
    # === 13. GANDHI ===
    {
        "id": "gandhi",
        "nombre": "Mahatma Gandhi",
        "tipo": "real",
        "genero": "masculino",
        "siglo": "XIX-XX",
        "epoca": "contemporaneo",
        "nacionalidad": "india",
        "area_principal": "politica",
        "subareas": ["espiritualidad", "activismo"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": False,
            "es_artista": False, "es_escritor": True, "es_militar": False,
            "es_lider": True, "es_religioso": True, "es_heroe": True,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": True,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": True,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_pacifista": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Su arma fue la no violencia, no las balas"}
        },
        "pistas": [
            "Caminó hasta el mar para tomar un puñado de sal prohibida",
            "Sin disparar un arma liberó a millones del yugo imperial"
        ]
    },
    
    # === 14. JUANA DE ARCO ===
    {
        "id": "juana_arco",
        "nombre": "Juana de Arco",
        "tipo": "real",
        "genero": "femenino",
        "siglo": "XV",
        "epoca": "medieval",
        "nacionalidad": "francesa",
        "area_principal": "militar",
        "subareas": ["religion", "historia"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": True,
            "es_lider": True, "es_religioso": True, "es_heroe": True,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": True,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_santa": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Fue canonizada por la Iglesia Católica siglos después de su muerte"}
        },
        "pistas": [
            "Voces celestiales la guiaron a vestir armadura de hombre",
            "Las llamas la consumieron pero su fe quedó inmortalizada"
        ]
    },
    
    # === 15. PABLO PICASSO ===
    {
        "id": "picasso",
        "nombre": "Pablo Picasso",
        "tipo": "real",
        "genero": "masculino",
        "siglo": "XIX-XX",
        "epoca": "contemporaneo",
        "nacionalidad": "española",
        "area_principal": "arte",
        "subareas": ["pintura", "escultura"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": False,
            "es_artista": True, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": True, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": True, "es_dramaturgo": True,
            "es_pintor": True, "es_escultor": True, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_cubista": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Rompió la realidad en fragmentos para volverla a armar"}
        },
        "pistas": [
            "Rompió la realidad en mil fragmentos geométricos de color",
            "El horror de la guerra grita eternamente en su lienzo más célebre"
        ]
    },
    
    # === 16. DON QUIJOTE ===
    {
        "id": "don_quijote",
        "nombre": "Don Quijote",
        "tipo": "ficticio",
        "genero": "masculino",
        "siglo": "XVII",
        "epoca": "moderna",
        "nacionalidad": "española",
        "area_principal": "literatura",
        "subareas": ["caballeria", "aventuras"],
        "universo": "Literatura",
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": True, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": True,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": True,
            "es_explorador": True, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_loco": {"respuesta_matiz": "Probablemente no", "aclaracion": "Vio gigantes donde otros veían molinos, pero su cordura era poética"}
        },
        "pistas": [
            "Confundió molinos de viento con gigantes temibles",
            "Su locura era más noble que la cordura de muchos"
        ]
    },
    
    # === 17. MULAN ===
    {
        "id": "mulan",
        "nombre": "Mulan",
        "tipo": "leyenda",
        "genero": "femenino",
        "siglo": "Antiguo",
        "epoca": "medieval",
        "nacionalidad": "china",
        "area_principal": "leyenda",
        "subareas": ["militar", "folklore"],
        "universo": "Leyenda",
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": True,
            "es_lider": True, "es_religioso": False, "es_heroe": True,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": True,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": True,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": True, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": True, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_real": {"respuesta_matiz": "Probablemente no", "aclaracion": "Basada en una leyenda, pero su historia ha inspirado generaciones"}
        },
        "pistas": [
            "Cortó su cabello y vistió armadura para salvar a su padre",
            "Durante años nadie supo que el soldado era una mujer"
        ]
    },
    
    # === 18. DARTH VADER ===
    {
        "id": "darth_vader",
        "nombre": "Darth Vader",
        "tipo": "ficticio",
        "genero": "masculino",
        "siglo": "Futuro",
        "epoca": "futurista",
        "nacionalidad": "tatooine",
        "area_principal": "cine",
        "subareas": ["ciencia_ficcion", "space_opera"],
        "universo": "Star Wars",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": True,
            "es_lider": True, "es_religioso": False, "es_heroe": False,
            "es_villano": True, "usa_tecnologia": True, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": True, "usa_mascara": True, "usa_armadura": True,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": True, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_humano": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Fue humano, pero la tecnología y el lado oscuro lo transformaron"}
        },
        "pistas": [
            "Su respiración mecánica anuncia la presencia del terror galáctico",
            "Cayó en la oscuridad pero un hijo lo redimió al final"
        ]
    },
    
    # === 19. SPIDERMAN ===
    {
        "id": "spiderman",
        "nombre": "Spider-Man",
        "tipo": "ficticio",
        "genero": "masculino",
        "siglo": "XX",
        "epoca": "contemporaneo",
        "nacionalidad": "estadounidense",
        "area_principal": "ficcion",
        "subareas": ["superheroes"],
        "universo": "Marvel",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": True,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": True,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": True,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": True, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": True, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": True, "es_fisico": True, "es_quimico": True,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": True, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_cientifico": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Peter Parker es un genio científico, aunque sus poderes no vienen de la ciencia"}
        },
        "pistas": [
            "Una picadura radioactiva le dio lo que la ciencia no pudo",
            "Con gran poder viene una responsabilidad aún mayor"
        ]
    },
    
    # === 20. HERMIONE GRANGER ===
    {
        "id": "hermione",
        "nombre": "Hermione Granger",
        "tipo": "ficticio",
        "genero": "femenino",
        "siglo": "XX",
        "epoca": "contemporaneo",
        "nacionalidad": "inglesa",
        "area_principal": "ficcion",
        "subareas": ["fantasia", "literatura", "cine"],
        "universo": "Harry Potter",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": True,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": True, "es_religioso": False, "es_heroe": True,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": True, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": True, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": True,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_la_mas_inteligente": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Su intelecto es su mayor magia"}
        },
        "pistas": [
            "Los libros son su mayor tesoro y su arma más poderosa",
            "Nacida sin magia pero convertida en la bruja más brillante"
        ]
    },
    
    # === 21. ARES ===
    {
        "id": "ares",
        "nombre": "Ares",
        "tipo": "mitologico",
        "genero": "masculino",
        "siglo": "Antiguo",
        "epoca": "antigua",
        "nacionalidad": "griega",
        "area_principal": "mitologia",
        "subareas": ["guerra", "religion"],
        "universo": "Mitología Griega",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": True,
            "es_lider": True, "es_religioso": True, "es_heroe": False,
            "es_villano": True, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": True, "tiene_barba": True, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": True,
            "puede_volar": False, "es_inmortal": True, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": True,
            "es_dios": True, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_bueno": {"respuesta_matiz": "Probablemente no", "aclaracion": "Dios de la guerra, no precisamente un pacifista"}
        },
        "pistas": [
            "Hijo de Zeus, pero su reino es la sangre y la batalla",
            "Su hermana Atenea lo vencía con estrategia donde él usaba fuerza bruta"
        ]
    },
    
    # === 22. ZEUS ===
    {
        "id": "zeus",
        "nombre": "Zeus",
        "tipo": "mitologico",
        "genero": "masculino",
        "siglo": "Antiguo",
        "epoca": "antigua",
        "nacionalidad": "griega",
        "area_principal": "mitologia",
        "subareas": ["religion", "poder"],
        "universo": "Mitología Griega",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": True, "es_religioso": True, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": True,
            "es_divino": True, "tiene_barba": True, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": True, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": True, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": True, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": True,
            "es_dios": True, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_fiel": {"respuesta_matiz": "Probablemente no", "aclaracion": "Rey de dioses, pero no precisamente un ejemplo de fidelidad"}
        },
        "pistas": [
            "Rey del Olimpo, su poder era el rayo y el trueno",
            "Se transformaba en animal para conquistar a sus amantes"
        ]
    },
    
    # === 23. ATENEA ===
    {
        "id": "atenea",
        "nombre": "Atenea",
        "tipo": "mitologico",
        "genero": "femenino",
        "siglo": "Antiguo",
        "epoca": "antigua",
        "nacionalidad": "griega",
        "area_principal": "mitologia",
        "subareas": ["sabiduria", "guerra"],
        "universo": "Mitología Griega",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": True,
            "es_artista": True, "es_escritor": True, "es_militar": True,
            "es_lider": True, "es_religioso": True, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": True, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": True,
            "puede_volar": False, "es_inmortal": True, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": True,
            "es_explorador": False, "es_inventor": True, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": True, "es_quimico": False,
            "es_matematico": True, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": True,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": True,
            "es_dios": True, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_pacifista": {"respuesta_matiz": "Probablemente no", "aclaracion": "Diosa de la guerra justa y la estrategia"}
        },
        "pistas": [
            "Nació de la cabeza de su padre, ya adulta y con armadura",
            "Su símbolo es el búho, representando la sabiduría"
        ]
    },
    
    # === 24. BEETHOVEN ===
    {
        "id": "beethoven",
        "nombre": "Ludwig van Beethoven",
        "tipo": "real",
        "genero": "masculino",
        "siglo": "XVIII-XIX",
        "epoca": "moderna",
        "nacionalidad": "alemana",
        "area_principal": "musica",
        "subareas": ["composicion", "piano"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": False,
            "es_artista": True, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": True,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": True, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "era_sordo": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Compuso sus obras más famosas sin poder escucharlas"}
        },
        "pistas": [
            "Su música atravesó el silencio de su propio mundo",
            "El destino llamó a su puerta con cinco notas inmortales"
        ]
    },
    
    # === 25. MOZART ===
    {
        "id": "mozart",
        "nombre": "Wolfgang Amadeus Mozart",
        "tipo": "real",
        "genero": "masculino",
        "siglo": "XVIII",
        "epoca": "moderna",
        "nacionalidad": "austriaca",
        "area_principal": "musica",
        "subareas": ["composicion", "piano"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": False,
            "es_artista": True, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": True,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": True,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": True, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "fue_un_niño_prodigio": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Componía música antes de saber atarse los zapatos"}
        },
        "pistas": [
            "Su música fluía como si los ángeles se la dictaran",
            "Murió joven, pero su Réquiem lo hizo inmortal"
        ]
    },
    
    # === 26. NEIL ARMSTRONG ===
    {
        "id": "neil_armstrong",
        "nombre": "Neil Armstrong",
        "tipo": "real",
        "genero": "masculino",
        "siglo": "XX",
        "epoca": "contemporaneo",
        "nacionalidad": "estadounidense",
        "area_principal": "exploracion",
        "subareas": ["astronautica", "ciencia"],
        "universo": None,
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": True, "es_cientifico": True,
            "es_artista": False, "es_escritor": False, "es_militar": True,
            "es_lider": False, "es_religioso": False, "es_heroe": True,
            "es_villano": False, "usa_tecnologia": True, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": True,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": True, "es_inventor": False, "es_compositor": False,
            "es_astronauta": True, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": True, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "caminó_en_la_luna": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Un pequeño paso para el hombre, un gran salto para la humanidad"}
        },
        "pistas": [
            "Su huella durará más que cualquier monumento en la Tierra",
            "Un pequeño paso para él, un gran salto para todos"
        ]
    },
    
    # === 27. FRANKENSTEIN ===
    {
        "id": "frankenstein",
        "nombre": "Frankenstein",
        "tipo": "ficticio",
        "genero": "masculino",
        "siglo": "XIX",
        "epoca": "moderna",
        "nacionalidad": "suiza",
        "area_principal": "literatura",
        "subareas": ["terror", "ciencia_ficcion"],
        "universo": "Literatura",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": True
        },
        "matices": {
            "es_el_monstruo": {"respuesta_matiz": "Probablemente no", "aclaracion": "El monstruo no tiene nombre; Frankenstein es el científico"}
        },
        "pistas": [
            "Su creador le dio vida, pero no amor",
            "Buscaba compañía, pero su aspecto lo condenó a la soledad"
        ]
    },
    
    # === 28. DRÁCULA ===
    {
        "id": "dracula",
        "nombre": "Drácula",
        "tipo": "ficticio",
        "genero": "masculino",
        "siglo": "XIX",
        "epoca": "moderna",
        "nacionalidad": "rumana",
        "area_principal": "literatura",
        "subareas": ["terror", "fantasia"],
        "universo": "Literatura",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": True,
            "es_lider": True, "es_religioso": False, "es_heroe": False,
            "es_villano": True, "usa_tecnologia": False, "tiene_identidad_secreta": True,
            "es_multimillonario": True, "es_famoso": True, "es_animal": True,
            "es_divino": False, "tiene_barba": True, "usa_gafas": False,
            "usa_capa": True, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": True, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": True
        },
        "matices": {
            "es_humano": {"respuesta_matiz": "Probablemente no", "aclaracion": "Fue humano, pero la inmortalidad lo cambió todo"}
        },
        "pistas": [
            "Teme a la cruz, al ajo y a la luz del día",
            "No se refleja en los espejos, pero su sed es eterna"
        ]
    },
    
    # === 29. ROBIN HOOD ===
    {
        "id": "robin_hood",
        "nombre": "Robin Hood",
        "tipo": "leyenda",
        "genero": "masculino",
        "siglo": "Medieval",
        "epoca": "medieval",
        "nacionalidad": "inglesa",
        "area_principal": "leyenda",
        "subareas": ["folklore", "aventuras"],
        "universo": "Leyenda",
        "rasgos_booleanos": {
            "tiene_poderes": False, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": True,
            "es_lider": True, "es_religioso": False, "es_heroe": True,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": True,
            "es_multimillonario": False, "es_famoso": True, "es_animal": False,
            "es_divino": False, "tiene_barba": True, "usa_gafas": False,
            "usa_capa": True, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": True, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": True, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": False, "es_monstruo": False
        },
        "matices": {
            "es_real": {"respuesta_matiz": "Probablemente no", "aclaracion": "Pudo haber existido un forajido, pero la leyenda es más grande"}
        },
        "pistas": [
            "Robaba a los ricos para dar a los pobres",
            "Su hogar era el bosque, y su enemigo, el sheriff"
        ]
    },
    
    # === 30. KING KONG ===
    {
        "id": "king_kong",
        "nombre": "King Kong",
        "tipo": "ficticio",
        "genero": "masculino",
        "siglo": "XX",
        "epoca": "contemporaneo",
        "nacionalidad": "isla_calavera",
        "area_principal": "cine",
        "subareas": ["aventuras", "monstruos"],
        "universo": "Cine",
        "rasgos_booleanos": {
            "tiene_poderes": True, "es_historico": False, "es_cientifico": False,
            "es_artista": False, "es_escritor": False, "es_militar": False,
            "es_lider": False, "es_religioso": False, "es_heroe": False,
            "es_villano": False, "usa_tecnologia": False, "tiene_identidad_secreta": False,
            "es_multimillonario": False, "es_famoso": True, "es_animal": True,
            "es_divino": False, "tiene_barba": False, "usa_gafas": False,
            "usa_capa": False, "usa_mascara": False, "usa_armadura": False,
            "puede_volar": False, "es_inmortal": False, "es_detective": False,
            "premios_nobel": False, "es_mago": False, "es_reina": False,
            "es_emperador": False, "es_faraon": False, "es_filosofo": False,
            "es_explorador": False, "es_inventor": False, "es_compositor": False,
            "es_astronauta": False, "es_presidente": False, "es_cientifico_nuclear": False,
            "es_biologo": False, "es_fisico": False, "es_quimico": False,
            "es_matematico": False, "es_poeta": False, "es_dramaturgo": False,
            "es_pintor": False, "es_escultor": False, "es_arquitecto": False,
            "es_musico": False, "es_actor": False, "es_director": False,
            "es_cantante": False, "es_deportista": False, "es_heroe_mitologico": False,
            "es_dios": False, "es_semidios": False, "es_titan": False,
            "es_gigante": True, "es_monstruo": True
        },
        "matices": {
            "es_una_amenaza": {"respuesta_matiz": "Probablemente sí", "aclaracion": "El monstruo que enamoró al mundo antes de caer"},
            "es_animal": {"respuesta_matiz": "Probablemente sí", "aclaracion": "Un gorila gigante, pero con corazón"}
        },
        "pistas": [
            "Nadie sabía que existía hasta que lo sacaron de su isla",
            "Escaló el edificio más alto de Nueva York por amor"
        ]
    }
]


# ===================================================================
# NORMALIZADOR DE TEXTO
# ===================================================================

class Normalizador:
    """Normaliza texto: minúsculas, sin tildes, sin signos, con sinónimos"""
    
    SINONIMOS = {
        r'\bitalian\b': 'italiano',
        r'\bde italia\b': 'italiano',
        r'\bingl?s\b': 'ingles',
        r'\bde inglaterra\b': 'ingles',
        r'\bfranc.s\b': 'frances',
        r'\bestadounidense\b': 'americano',
        r'\bde eeuu\b': 'americano',
        r'\bsuperpoderes?\b': 'tiene_poderes',
        r'\bpoderes?\s+(especiales|sobrenaturales)?\b': 'tiene_poderes',
        r'\bpuede volar\b': 'puede_volar',
        r'\bvuela\b': 'puede_volar',
        r'\bhombre\b|\bvarón\b': 'masculino',
        r'\bmujer\b|\bdama\b': 'femenino',
        r'\bexistió\b|\bexistio\b': 'real',
        r'\binventado\b|\bimaginario\b': 'ficticio',
        r'\bcientifico\b|\bcientifica\b': 'cientifico',
        r'\bartista\b|\bpintor\b': 'artista',
        r'\bescritor\b|\bescritora\b': 'escritor',
        r'\bmilitar\b|\bsoldado\b': 'militar',
        r'\bdetective\b': 'detective',
        r'\brenacimiento\b': 'renacimiento',
        r'\bcontemporaneo\b|\bactual\b': 'contemporaneo',
        r'\bmedieval\b|\bedad media\b': 'medieval',
        r'\bdc comics?\b|\bdc\b': 'DC',
        r'\bmarvel\b': 'Marvel',
        r'\btolkien\b|\blotr\b': 'Tolkien',
        r'\bharry potter\b|\bhp\b': 'Harry Potter',
        r'\busa gafas\b|\blentes\b': 'usa_gafas',
        r'\btiene barba\b': 'tiene_barba',
        r'\bmillonario\b|\brico\b': 'multimillonario',
        r'\bh?umano?\b': 'humano',
        r'\binmortal\b': 'inmortal',
        r'\bheroe\b': 'heroe',
        r'\bvillano\b': 'villano',
        r'\blider\b|\blíder\b': 'lider',
        r'\bdivino\b': 'divino',
        r'\banimal\b': 'animal',
        r'\bgigante\b': 'gigante',
        r'\bmonstruo\b': 'monstruo',
    }
    
    @staticmethod
    def normalizar(texto: str) -> str:
        """Pipeline completo de normalización"""
        if not texto:
            return ""
        
        texto = texto.lower()
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
        signos = '¿?¡!.,;:()[]{}"\'-'
        for signo in signos:
            texto = texto.replace(signo, ' ')
        texto = ' '.join(texto.split())
        
        for patron, reemplazo in Normalizador.SINONIMOS.items():
            texto = re.sub(patron, reemplazo, texto)
        
        return texto


# ===================================================================
# CLASIFICADOR DE PREGUNTAS
# ===================================================================

class CategoriaPregunta(Enum):
    IDENTIDAD = "identidad"
    ATRIBUTO_SIMPLE = "atributo_simple"
    ATRIBUTO_BOOLEANO = "atributo_booleano"
    FUERA_DOMINIO = "fuera_dominio"


class Clasificador:
    """Clasifica preguntas en categorías y mapea a campos"""
    
    MAPEO_CAMPOS = {
        r'^\s*(el|tu)?\s*personaje\s*es\s*(.+?)\s*\?*\s*$': ('nombre', CategoriaPregunta.IDENTIDAD),
        r'\breal\b': ('tipo', CategoriaPregunta.ATRIBUTO_SIMPLE),
        r'\bficticio\b': ('tipo', CategoriaPregunta.ATRIBUTO_SIMPLE),
        r'\bmasculino\b|\bhombre\b': ('genero', CategoriaPregunta.ATRIBUTO_SIMPLE),
        r'\bfemenino\b|\bmujer\b': ('genero', CategoriaPregunta.ATRIBUTO_SIMPLE),
        r'\bnacionalidad\b|\bde\s+([a-z]+)\b': ('nacionalidad', CategoriaPregunta.ATRIBUTO_SIMPLE),
        r'\bitaliano\b|\bingles\b|\bfrances\b|\bamericana?\b': ('nacionalidad', CategoriaPregunta.ATRIBUTO_SIMPLE),
        r'\bépoca\b|\bepoca\b|\bsiglo\b': ('epoca', CategoriaPregunta.ATRIBUTO_SIMPLE),
        r'\brenacimiento\b|\bcontemporaneo\b|\bmedieval\b': ('epoca', CategoriaPregunta.ATRIBUTO_SIMPLE),
        r'\buniverso\b': ('universo', CategoriaPregunta.ATRIBUTO_SIMPLE),
        r'\bdc\b|\bmarvel\b|\btolkien\b': ('universo', CategoriaPregunta.ATRIBUTO_SIMPLE),
        r'\barea\b|\bárea\b': ('area_principal', CategoriaPregunta.ATRIBUTO_SIMPLE),
        r'\bciencia\b|\barte\b|\bpolitica\b|\bfantasia\b': ('area_principal', CategoriaPregunta.ATRIBUTO_SIMPLE),
    }
    
    MAPEO_RASGOS = {
        r'\btiene\s+poderes?\b': 'tiene_poderes',
        r'\bes\s+cientifico\b': 'es_cientifico',
        r'\bes\s+artista\b': 'es_artista',
        r'\bes\s+escritor\b': 'es_escritor',
        r'\bes\s+militar\b': 'es_militar',
        r'\bes\s+lider\b': 'es_lider',
        r'\bes\s+heroe\b': 'es_heroe',
        r'\bes\s+villano\b': 'es_villano',
        r'\busa\s+tecnologia\b': 'usa_tecnologia',
        r'\btiene\s+identidad\s+secreta\b': 'tiene_identidad_secreta',
        r'\bes\s+multimillonario\b': 'es_multimillonario',
        r'\bes\s+famoso\b': 'es_famoso',
        r'\bes\s+animal\b': 'es_animal',
        r'\bes\s+divino\b': 'es_divino',
        r'\btiene\s+barba\b': 'tiene_barba',
        r'\busa\s+gafas\b': 'usa_gafas',
        r'\busa\s+capa\b': 'usa_capa',
        r'\busa\s+mascara\b': 'usa_mascara',
        r'\bpuede\s+volar\b': 'puede_volar',
        r'\bes\s+inmortal\b': 'es_inmortal',
        r'\bes\s+detective\b': 'es_detective',
        r'\btiene\s+premio\s+nobel\b': 'premios_nobel',
        r'\bes\s+humano\b': 'es_humano',
        r'\bes\s+gigante\b': 'es_gigante',
        r'\bes\s+monstruo\b': 'es_monstruo',
    }
    
    @classmethod
    def clasificar(cls, pregunta: str) -> Tuple[Optional[str], Optional[Any], CategoriaPregunta]:
        pregunta_norm = Normalizador.normalizar(pregunta)
        
        for patron, (campo, categoria) in cls.MAPEO_CAMPOS.items():
            match = re.search(patron, pregunta_norm)
            if match:
                if categoria == CategoriaPregunta.IDENTIDAD and len(match.groups()) > 0:
                    return (campo, match.group(1).strip(), categoria)
                return (campo, None, categoria)
        
        for patron, rasgo in cls.MAPEO_RASGOS.items():
            if re.search(patron, pregunta_norm):
                return (rasgo, True, CategoriaPregunta.ATRIBUTO_BOOLEANO)
        
        return (None, None, CategoriaPregunta.FUERA_DOMINIO)


# ===================================================================
# REGISTRO DE HUECOS
# ===================================================================

class HuecosRegistry:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._inicializar()
        return cls._instance
    
    def _inicializar(self):
        self.archivo = REGISTRO_HUECOS_FILE
        self.registros = self._cargar()
    
    def _cargar(self) -> List[Dict]:
        try:
            if os.path.exists(self.archivo):
                with open(self.archivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return []
    
    def _guardar(self):
        try:
            if len(self.registros) > 1000:
                self.registros = self.registros[-1000:]
            with open(self.archivo, 'w', encoding='utf-8') as f:
                json.dump(self.registros, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def registrar(self, pregunta: str, personaje: Dict, motivo: str):
        self.registros.append({
            "timestamp": datetime.now().isoformat(),
            "pregunta_original": pregunta,
            "pregunta_normalizada": Normalizador.normalizar(pregunta),
            "personaje": personaje.get("nombre", "desconocido"),
            "tipo_personaje": personaje.get("tipo", "desconocido"),
            "motivo": motivo
        })
        self._guardar()
        print(f"📝 Hueco: '{pregunta}' para {personaje.get('nombre')} ({motivo})")
    
    def obtener_todos(self) -> List[Dict]:
        return self.registros
    
    def obtener_ultimos(self, n: int = 50) -> List[Dict]:
        return self.registros[-n:]


huecos = HuecosRegistry()


# ===================================================================
# MOTOR DE COHERENCIA (Memoria por partida)
# ===================================================================

class MemoriaPartida:
    def __init__(self, session_id: str, personaje: Dict):
        self.session_id = session_id
        self.personaje_nombre = personaje.get("nombre")
        self.preguntas = []
        self.respuestas = []
        self.respuestas_por_campo = {}
        self.no_consecutivos = 0
        self.preguntas_restantes = MAX_PREGUNTAS
    
    def registrar(self, pregunta: str, respuesta: str, campo: str = None):
        self.preguntas.append(pregunta)
        self.respuestas.append(respuesta)
        self.preguntas_restantes -= 1
        
        if campo:
            self.respuestas_por_campo[campo] = respuesta
        
        if respuesta == "No":
            self.no_consecutivos += 1
        else:
            self.no_consecutivos = 0
    
    def validar_coherencia(self, campo: str, respuesta_sugerida: str) -> Tuple[bool, Optional[str]]:
        if campo in self.respuestas_por_campo:
            respuesta_anterior = self.respuestas_por_campo[campo]
            if respuesta_anterior != respuesta_sugerida:
                return False, "Eso contradice información previa."
        return True, None
    
    def necesita_orientacion(self) -> bool:
        return self.no_consecutivos >= NO_CONSECUTIVOS_ORIENTACION
    
    def reset_orientacion(self):
        self.no_consecutivos = 0
    
    def puede_seguir(self) -> bool:
        return self.preguntas_restantes > 0


class MemoryManager:
    def __init__(self):
        self.memorias: Dict[str, MemoriaPartida] = {}
    
    def obtener(self, session_id: str, personaje: Dict = None) -> Optional[MemoriaPartida]:
        if session_id not in self.memorias and personaje:
            self.memorias[session_id] = MemoriaPartida(session_id, personaje)
        return self.memorias.get(session_id)
    
    def limpiar(self, session_id: str):
        if session_id in self.memorias:
            del self.memorias[session_id]


memory_manager = MemoryManager()


# ===================================================================
# MOTOR DE RESPUESTAS DEL ORÁCULO
# ===================================================================

class Oráculo:
    @staticmethod
    def responder(personaje: Dict, campo: str, valor_esperado: Any, 
                 categoria: CategoriaPregunta) -> Dict:
        
        if categoria == CategoriaPregunta.IDENTIDAD:
            return {"answer": "No lo sé", "clarification": ""}
        
        matices = personaje.get("matices", {})
        if campo in matices:
            matiz = matices[campo]
            return {
                "answer": matiz["respuesta_matiz"],
                "clarification": matiz["aclaracion"]
            }
        
        if categoria == CategoriaPregunta.ATRIBUTO_SIMPLE:
            valor_real = personaje.get(campo)
            if valor_real is None:
                return {"answer": "No lo sé", "clarification": ""}
            
            if valor_esperado is not None:
                valor_real_norm = Normalizador.normalizar(str(valor_real))
                valor_esp_norm = Normalizador.normalizar(str(valor_esperado))
                return {"answer": "Sí" if valor_real_norm == valor_esp_norm else "No", "clarification": ""}
            
            return {"answer": "No lo sé", "clarification": ""}
        
        if categoria == CategoriaPregunta.ATRIBUTO_BOOLEANO:
            rasgos = personaje.get("rasgos_booleanos", {})
            valor_real = rasgos.get(campo)
            
            if valor_real is None:
                return {"answer": "No lo sé", "clarification": ""}
            
            return {"answer": "Sí" if valor_real == valor_esperado else "No", "clarification": ""}
        
        return {"answer": "No lo sé", "clarification": ""}
    
    @staticmethod
    def generar_orientacion(personaje: Dict) -> str:
        if personaje.get("tipo") == "real":
            return "Quizás deberías explorar su época, nacionalidad o área de especialización."
        else:
            return "Quizás deberías explorar su universo, origen o si tiene habilidades especiales."


oraculo = Oráculo()


# ===================================================================
# DETECTOR DE ADIVINANZAS
# ===================================================================

class AdivinanzaDetector:
    @staticmethod
    def es_intento(pregunta: str) -> bool:
        pregunta_lower = pregunta.lower()
        patrones = [
            r'^tu personaje es (.*?)\??$',
            r'^es (.*?)\??$',
            r'^el personaje es (.*?)\??$',
            r'^el personaje se llama (.*?)\??$',
            r'^se llama (.*?)\??$'
        ]
        for patron in patrones:
            if re.match(patron, pregunta_lower):
                return True
        return False
    
    @staticmethod
    def extraer_nombre(pregunta: str) -> str:
        pregunta_lower = pregunta.lower()
        for prefijo in ['tu personaje es ', 'es ', 'el personaje es ', 
                       'el personaje se llama ', 'se llama ']:
            if pregunta_lower.startswith(prefijo):
                nombre = pregunta_lower[len(prefijo):].strip(' ?')
                return nombre
        return pregunta_lower.strip(' ?')
    
    @staticmethod
    def comparar(nombre1: str, nombre2: str) -> bool:
        n1 = Normalizador.normalizar(nombre1)
        n2 = Normalizador.normalizar(nombre2)
        
        if n1 == n2:
            return True
        
        ratio = SequenceMatcher(None, n1, n2).ratio()
        return ratio >= UMBRAL_SIMILITUD


adivinanza = AdivinanzaDetector()


# ===================================================================
# RAZONADOR ESTRATÉGICO (NUEVO - para sugerencias)
# ===================================================================

@dataclass
class EstadoConocimiento:
    confirmado: Dict[str, str] = field(default_factory=dict)
    descartado: Dict[str, Set[str]] = field(default_factory=dict)
    sospechas: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    historial: List[Tuple[str, str, str]] = field(default_factory=list)
    
    def inicializar(self):
        self.descartado = {
            "tipo": set(), "genero": set(), "especie": set(), "epoca": set(),
            "origen": set(), "universo": set(), "poderes": set(), "profesion": set(),
            "tamaño": set(),
        }
    
    def registrar(self, pregunta: str, respuesta: str, campo: str = None, valor: str = None):
        self.historial.append((pregunta, respuesta, campo or "desconocido"))
        
        if respuesta == "Sí" and campo and valor:
            self.confirmado[campo] = valor
        elif respuesta == "No" and campo and valor:
            self.descartado.setdefault(campo, set()).add(valor)
        elif "Probablemente" in respuesta and campo:
            self.sospechas[campo] = (valor, respuesta)


class BaseConocimiento:
    def __init__(self, personajes: List[Dict]):
        self.personajes = personajes
    
    def posibles_segun(self, conocimiento: EstadoConocimiento) -> List[Dict]:
        candidatos = self.personajes.copy()
        
        for campo, valor in conocimiento.confirmado.items():
            candidatos = [p for p in candidatos if self._coincide(p, campo, valor)]
        
        for campo, valores in conocimiento.descartado.items():
            for valor in valores:
                candidatos = [p for p in candidatos if not self._coincide(p, campo, valor)]
        
        return candidatos
    
    def _coincide(self, personaje: Dict, campo: str, valor: str) -> bool:
        if campo == "genero":
            return personaje.get("genero") == valor
        elif campo == "tipo":
            return personaje.get("tipo") == valor
        elif campo == "especie":
            if valor == "animal":
                return personaje.get("rasgos_booleanos", {}).get("es_animal", False)
            elif valor == "divino":
                return personaje.get("rasgos_booleanos", {}).get("es_divino", False)
            elif valor == "humano":
                return personaje.get("rasgos_booleanos", {}).get("es_humano", False)
        elif campo == "tamaño":
            if valor == "gigante":
                return personaje.get("rasgos_booleanos", {}).get("es_gigante", False)
        elif campo == "poderes":
            if valor == "si":
                return personaje.get("rasgos_booleanos", {}).get("tiene_poderes", False)
        return False


class Estratega:
    PREGUNTAS_POR_CATEGORIA = {
        "tipo": ["¿Es una persona real?", "¿Es un personaje ficticio?", "¿Es un ser mitológico?"],
        "genero": ["¿Es hombre?", "¿Es mujer?"],
        "especie": ["¿Es humano?", "¿Es un animal?", "¿Es un ser divino?"],
        "epoca": ["¿Es de época antigua?", "¿Vivió en la Edad Media?", "¿Es de la era moderna?"],
        "origen": ["¿Es de Europa?", "¿Es de América?", "¿Es de otro mundo?"],
        "universo": ["¿Pertenece a DC?", "¿Pertenece a Marvel?", "¿Es de Star Wars?"],
        "poderes": ["¿Tiene poderes?", "¿Puede volar?", "¿Es inmortal?"],
        "profesion": ["¿Es un héroe?", "¿Es un villano?", "¿Es científico?"],
        "tamaño": ["¿Es de tamaño normal?", "¿Es gigante?"],
    }
    
    def __init__(self, base_conocimiento: BaseConocimiento):
        self.base = base_conocimiento
    
    def sugerir(self, conocimiento: EstadoConocimiento, max_sug: int = 5) -> List[str]:
        candidatos = self.base.posibles_segun(conocimiento)
        num_posibles = len(candidatos)
        
        if num_posibles > 10:
            return self._preguntas_amplias(conocimiento, max_sug)
        elif num_posibles > 3:
            return self._preguntas_discriminantes(candidatos, conocimiento, max_sug)
        else:
            return self._preguntas_finas(max_sug)
    
    def _preguntas_amplias(self, conocimiento: EstadoConocimiento, max_sug: int) -> List[str]:
        sugerencias = []
        categorias = ["tipo", "especie", "epoca", "universo", "poderes"]
        
        for cat in categorias:
            if cat not in conocimiento.confirmado:
                for p in self.PREGUNTAS_POR_CATEGORIA[cat]:
                    if not self._ya_preguntada(p, conocimiento):
                        sugerencias.append(p)
                        break
            if len(sugerencias) >= max_sug:
                break
        
        return sugerencias[:max_sug]
    
    def _preguntas_discriminantes(self, candidatos: List[Dict], conocimiento: EstadoConocimiento, max_sug: int) -> List[str]:
        sugerencias = []
        
        if len(candidatos) == 2:
            a, b = candidatos[0], candidatos[1]
            if a.get("universo") != b.get("universo"):
                sugerencias.append("¿Pertenece a algún universo conocido?")
            if a.get("rasgos_booleanos", {}).get("tiene_poderes") != b.get("rasgos_booleanos", {}).get("tiene_poderes"):
                sugerencias.append("¿Tiene poderes?")
        
        return sugerencias[:max_sug] or self._preguntas_finas(max_sug)
    
    def _preguntas_finas(self, max_sug: int) -> List[str]:
        return [
            "¿Es famoso mundialmente?",
            "¿Aparece en películas?",
            "¿Tiene alguna característica física distintiva?"
        ][:max_sug]
    
    def _ya_preguntada(self, pregunta: str, conocimiento: EstadoConocimiento) -> bool:
        pregunta_norm = Normalizador.normalizar(pregunta)
        for p, _, _ in conocimiento.historial:
            if Normalizador.normalizar(p) == pregunta_norm:
                return True
        return False


class RazonadorOracle:
    def __init__(self, personajes: List[Dict]):
        self.base = BaseConocimiento(personajes)
        self.estratega = Estratega(self.base)
        self.cuadernos: Dict[str, EstadoConocimiento] = {}
    
    def iniciar_partida(self, session_id: str):
        cuaderno = EstadoConocimiento()
        cuaderno.inicializar()
        self.cuadernos[session_id] = cuaderno
    
    def registrar_interaccion(self, session_id: str, pregunta: str, respuesta: str, campo: str = None, valor: str = None):
        if session_id in self.cuadernos:
            self.cuadernos[session_id].registrar(pregunta, respuesta, campo, valor)
    
    def obtener_sugerencias(self, session_id: str, max_sug: int = 5) -> List[str]:
        if session_id not in self.cuadernos:
            return ["¿Es una persona real?", "¿Es hombre o mujer?", "¿De qué época es?"]
        return self.estratega.sugerir(self.cuadernos[session_id], max_sug)


razonador = RazonadorOracle(PERSONAJES)


# ===================================================================
# ENDPOINTS DE LA API
# ===================================================================

@app.route('/api/oracle', methods=['POST'])
def oracle():
    try:
        data = request.get_json()
        action = data.get('action')
        session_id = data.get('session_id', request.remote_addr)
        
        if action == 'start':
            character = random.choice(PERSONAJES)
            memory_manager.limpiar(session_id)
            razonador.iniciar_partida(session_id)
            return jsonify({
                'character': character,
                'message': 'He concebido mi enigma. Comienza a preguntar.',
                'session_id': session_id
            })
        
        elif action == 'ask':
            question = data.get('question', '').strip()
            character = data.get('character', {})
            
            if not question:
                return jsonify({'answer': 'No lo sé', 'clarification': ''})
            
            memoria = memory_manager.obtener(session_id, character)
            if not memoria.puede_seguir():
                return jsonify({'answer': 'Has agotado tus preguntas. Debes adivinar.', 'clarification': ''})
            
            if adivinanza.es_intento(question):
                nombre_guess = adivinanza.extraer_nombre(question)
                nombre_real = character.get("nombre", "")
                
                if adivinanza.comparar(nombre_guess, nombre_real):
                    return jsonify({'answer': '✅ Correcto. Has resuelto el enigma.', 'clarification': ''})
                else:
                    memoria.registrar(question, "No")
                    razonador.registrar_interaccion(session_id, question, "No")
                    return jsonify({'answer': 'No.', 'clarification': ''})
            
            campo, valor_esperado, categoria = Clasificador.clasificar(question)
            
            if categoria == CategoriaPregunta.FUERA_DOMINIO:
                huecos.registrar(question, character, "no_clasificable")
                memoria.registrar(question, "No lo sé")
                razonador.registrar_interaccion(session_id, question, "No lo sé")
                
                if memoria.necesita_orientacion():
                    memoria.reset_orientacion()
                    return jsonify({'answer': oraculo.generar_orientacion(character), 'clarification': ''})
                
                return jsonify({'answer': 'No lo sé. ¿Podrías reformularlo?', 'clarification': ''})
            
            respuesta = oraculo.responder(character, campo, valor_esperado, categoria)
            
            es_coherente, error = memoria.validar_coherencia(campo, respuesta["answer"])
            if not es_coherente:
                return jsonify({'answer': error, 'clarification': ''})
            
            memoria.registrar(question, respuesta["answer"], campo)
            razonador.registrar_interaccion(session_id, question, respuesta["answer"], campo, valor_esperado)
            
            if memoria.necesita_orientacion():
                memoria.reset_orientacion()
                return jsonify({'answer': oraculo.generar_orientacion(character), 'clarification': ''})
            
            return jsonify(respuesta)
        
        elif action == 'guess':
            guess = data.get('guess', '').strip()
            character = data.get('character', {})
            character_name = character.get('nombre', '')
            
            if adivinanza.comparar(guess, character_name):
                return jsonify({'correct': True, 'character': character_name})
            else:
                return jsonify({'correct': False, 'character': character_name})
        
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
        
        elif action == 'suggestions':
            suggestions = razonador.obtener_sugerencias(session_id)
            return jsonify({'suggestions': suggestions})
        
        else:
            return jsonify({'error': 'Acción no válida'}), 400
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/huecos', methods=['GET'])
def ver_huecos():
    return jsonify({
        'total': len(huecos.obtener_todos()),
        'huecos': huecos.obtener_ultimos(50)
    })


@app.route('/exportar_huecos', methods=['GET'])
def exportar_huecos():
    try:
        if os.path.exists(REGISTRO_HUECOS_FILE):
            return send_file(REGISTRO_HUECOS_FILE, as_attachment=True, download_name='huecos.json')
        return jsonify({'error': 'No hay huecos'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'personajes': len(PERSONAJES),
        'version': 'Definitiva + Razonamiento Estratégico'
    })


@app.route('/')
def home():
    return """
    <html>
    <head><title>The Oracle</title></head>
    <body style="font-family:sans-serif; background:#000; color:#0f0; padding:20px; text-align:center;">
        <h1 style="color:#ff00ff;">🧠 THE ORACLE</h1>
        <p>Versión DEFINITIVA + Razonamiento Estratégico</p>
        <p>✅ 30 personajes</p>
        <p>✅ Razonamiento lógico para sugerencias</p>
        <p>✅ Memoria por partida + Coherencia</p>
        <p>✅ Registro de huecos</p>
        <p>📊 <a href="/huecos" style="color:#0f0;">Ver huecos</a></p>
    </body>
    </html>
    """


# ===================================================================
# EJECUCIÓN
# ===================================================================

if __name__ == '__main__':
    import os
    print("=" * 80)
    print("🧠 THE ORACLE - Backend")
    print("=" * 80)
    print(f"📡 Servidor: http://0.0.0.0:5000")
    print(f"🎭 Personajes: {len(PERSONAJES)}")
    print("=" * 80)
    
    # Puerto para producción
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
