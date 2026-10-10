"""Embeddings: convierte texto en vectores. Lo único que hace IA aquí."""
import numpy as np
from fastembed import TextEmbedding

import config

_modelo = None


def modelo() -> TextEmbedding:
    """Carga el modelo una sola vez (tarda ~20s la primera vez: lo descarga)."""
    global _modelo
    if _modelo is None:
        _modelo = TextEmbedding(config.MODELO, cache_dir=config.CACHE_MODELO)
    return _modelo


def vectorizar(textos: list[str]) -> np.ndarray:
    """Devuelve una matriz (n, 384) con los vectores YA normalizados.

    Normalizarlos aquí hace que la similitud coseno sea un simple producto
    punto más adelante. Un detalle, pero ahorra errores.
    """
    v = np.array(list(modelo().embed(textos)), dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)
