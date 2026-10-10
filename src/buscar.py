#!/usr/bin/env python3
"""Paso 2 del RAG: la búsqueda. Esto es la R de «retrieval».

Uso:
    ./rag buscar "¿qué es un Service Domain?"
"""
import sys

try:
    import numpy as np
    import config
    import embed
    import store
except ImportError as e:
    raise SystemExit(
        f"Falta la dependencia '{e.name}': estás usando el Python del sistema,\n"
        "no el del proyecto.\n\n"
        "Usa el lanzador:      ./rag buscar ...\n"
        "O activa el entorno:  source .venv/bin/activate && export PYTHONPATH=src"
    )


def buscar(pregunta: str, k: int = None, minimo: float = None) -> list[tuple[float, dict]]:
    """Devuelve hasta k fragmentos relevantes, con su puntaje.

    Puede devolver menos de k, o ninguno: los que no llegan a `minimo` se
    descartan. Devolver una lista vacía es una respuesta válida y útil —
    significa que el corpus no cubre la pregunta.

    Fuerza bruta: compara contra todos. Suena mal y no lo es — 50.000
    fragmentos son 73 MB y el producto punto tarda milisegundos. Un índice
    aproximado (HNSW, k-NN de OpenSearch) solo paga por encima de eso.
    """
    chunks, vectores = store.abrir().leer_chunks()
    if not chunks:
        sys.exit("El almacén está vacío. Corre primero: python src/ingest.py")

    k = config.TOP_K if k is None else k
    minimo = config.MINIMO if minimo is None else minimo

    q = embed.vectorizar([pregunta])[0]
    # Los vectores ya vienen normalizados, así que el producto punto ES el coseno.
    puntajes = vectores @ q
    mejores = np.argsort(-puntajes)[:k]
    return [(float(puntajes[i]), chunks[i]) for i in mejores
            if puntajes[i] >= minimo]


def mejor_puntaje(pregunta: str) -> float:
    """El puntaje del fragmento más parecido, pase o no el umbral.

    Sirve para diagnosticar: si una pregunta legítima no devuelve nada, esto te
    dice qué tan lejos quedó y si vale la pena bajar `MINIMO`.
    """
    chunks, vectores = store.abrir().leer_chunks()
    if not chunks:
        return 0.0
    return float(max(vectores @ embed.vectorizar([pregunta])[0]))


def main():
    if len(sys.argv) < 2:
        sys.exit('Uso: python src/buscar.py "tu pregunta"')
    pregunta = " ".join(sys.argv[1:])

    print(f"\nPregunta: {pregunta}\n" + "─" * 62)
    resultados = buscar(pregunta)

    if not resultados:
        print(f"\nNingún fragmento pasa el umbral de {config.MINIMO}.")
        print(f"El más parecido quedó en {mejor_puntaje(pregunta):.3f}.")
        print("\nO el corpus no cubre esto, o MINIMO está muy alto "
              "(se ajusta en src/config.py).\n")
        return

    for puntaje, c in resultados:
        print(f"\n[{puntaje:.3f}] {c['doc']} · {c['id']}")
        print("  " + c["texto"][:220].replace("\n", " ") + "…")
    print()


if __name__ == "__main__":
    main()
