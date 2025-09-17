#!/bin/bash

# Instala las dependencias
pip install -r requirements.txt

# Inicia el servidor
uvicorn main:app --host 0.0.0.0 --port $PORT
