"""Configuración única del RAG.

El truco de este proyecto: el código no sabe si habla con archivos locales o
con Floci. Lo decide `RAG_BACKEND`, y nada más cambia.
"""
import os

# "local" = archivos en disco (funciona hoy, sin Docker).
# "floci" = S3 + DynamoDB emulados por Floci en localhost:4566.
BACKEND = os.environ.get("RAG_BACKEND", "local")

# Floci expone todo AWS en un solo puerto.
ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
REGION = os.environ.get("AWS_REGION", "us-east-1")

BUCKET = "rag-docs"      # S3: los documentos originales
TABLA = "rag-chunks"     # DynamoDB: los fragmentos + sus vectores

# Multilingüe y pequeño: 0.22 GB, 384 dimensiones. Corre en CPU.
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DIMS = 384

# Dónde queda el modelo descargado. Por defecto fastembed usa /tmp, que se
# borra al reiniciar: se bajarían los 241 MB otra vez en cada arranque.
CACHE_MODELO = os.path.expanduser(
    os.environ.get("FASTEMBED_CACHE", "~/.cache/fastembed"))

# Tamaño de fragmento en caracteres, y cuánto se solapan.
CHUNK = 800
SOLAPE = 150

# Cuántos fragmentos se le pasan al modelo, como máximo.
TOP_K = 4

# Y el mínimo de similitud para que uno entre. Sin este corte, `k` fijo mete
# relleno: fragmentos que no hablan del tema pero llenan el cupo. Eso diluye la
# señal, multiplica los tokens que pagas y le da al modelo material para
# mezclar conceptos que no van juntos.
#
# 0.40 es un punto de partida, no una verdad. Súbelo si ves relleno en las
# respuestas; bájalo si te quedas sin fragmentos en preguntas legítimas.
MINIMO = 0.40
