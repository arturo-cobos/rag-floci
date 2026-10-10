#!/usr/bin/env python3
"""Paso 1 del RAG: meter los documentos al almacén.

Lee ./docs, los parte en fragmentos, los convierte en vectores y los guarda.
Corre esto cada vez que cambien los documentos.
"""
import pathlib
import sys

try:
    import config
    import embed
    import store
except ImportError as e:
    raise SystemExit(
        f"Falta la dependencia '{e.name}': estás usando el Python del sistema,\n"
        "no el del proyecto.\n\n"
        "Usa el lanzador:      ./rag ingest ...\n"
        "O activa el entorno:  source .venv/bin/activate && export PYTHONPATH=src"
    )

DOCS = pathlib.Path(__file__).parent.parent / "docs"


def partir(texto: str) -> list[str]:
    """Parte por párrafos, juntando hasta ~CHUNK caracteres con solape.

    Partir por párrafos y no por número fijo de caracteres evita cortar frases
    a la mitad, que es lo que más daña la calidad de la búsqueda.
    """
    parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    trozos, actual = [], ""
    for p in parrafos:
        if actual and len(actual) + len(p) > config.CHUNK:
            trozos.append(actual)
            actual = actual[-config.SOLAPE:] + "\n\n" + p  # el solape da contexto
        else:
            actual = f"{actual}\n\n{p}" if actual else p
    if actual:
        trozos.append(actual)
    return trozos


def main():
    archivos = sorted(DOCS.glob("*.md")) + sorted(DOCS.glob("*.txt"))
    if not archivos:
        sys.exit(f"No hay documentos en {DOCS}/ — pon ahí tus .md o .txt")

    alm = store.abrir()
    print(f"Almacén: {alm.nombre}\n" + "─" * 62)

    chunks = []
    for a in archivos:
        texto = a.read_text()
        alm.guardar_documento(a.name, texto)
        trozos = partir(texto)
        for i, t in enumerate(trozos):
            chunks.append({"id": f"{a.stem}#{i}", "doc": a.name, "texto": t})
        print(f"  {a.name:34s} {len(texto):6d} car  →  {len(trozos)} fragmentos")

    print(f"\nVectorizando {len(chunks)} fragmentos…")
    vectores = embed.vectorizar([c["texto"] for c in chunks])
    alm.guardar_chunks(chunks, vectores)

    print(f"Listo: {len(chunks)} fragmentos de {len(archivos)} documentos, "
          f"{vectores.shape[1]} dimensiones cada uno.")


if __name__ == "__main__":
    main()
