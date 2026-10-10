#!/usr/bin/env python3
"""Paso 2 del RAG: la búsqueda. Esto es la R de «retrieval».

Uso:
    python src/buscar.py "¿qué es un Service Domain?"
"""
import sys

try:
    import numpy as np
    import embed
    import store
except ImportError as e:
    raise SystemExit(
        f"Falta la dependencia '{e.name}': estás usando el Python del sistema,\n"
        "no el del proyecto.\n\n"
        "Usa el lanzador:      ./rag buscar ...\n"
        "O activa el entorno:  source .venv/bin/activate && export PYTHONPATH=src"
    )


def buscar(pregunta: str, k: int = 4) -> list[tuple[float, dict]]:
    """Devuelve los k fragmentos más parecidos, con su puntaje.

    Fuerza bruta: compara contra todos. Suena mal y no lo es — 50.000
    fragmentos son 73 MB y el producto punto tarda milisegundos. Un índice
    aproximado (HNSW, k-NN de OpenSearch) solo paga por encima de eso.
    """
    chunks, vectores = store.abrir().leer_chunks()
    if not chunks:
        sys.exit("El almacén está vacío. Corre primero: python src/ingest.py")

    q = embed.vectorizar([pregunta])[0]
    # Los vectores ya vienen normalizados, así que el producto punto ES el coseno.
    puntajes = vectores @ q
    mejores = np.argsort(-puntajes)[:k]
    return [(float(puntajes[i]), chunks[i]) for i in mejores]


def main():
    if len(sys.argv) < 2:
        sys.exit('Uso: python src/buscar.py "tu pregunta"')
    pregunta = " ".join(sys.argv[1:])

    print(f"\nPregunta: {pregunta}\n" + "─" * 62)
    for puntaje, c in buscar(pregunta):
        print(f"\n[{puntaje:.3f}] {c['doc']} · {c['id']}")
        print("  " + c["texto"][:220].replace("\n", " ") + "…")
    print()


if __name__ == "__main__":
    main()
