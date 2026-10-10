#!/usr/bin/env python3
"""Paso 3 del RAG: la G de «generation».

Recupera los fragmentos relevantes y le pide a Claude que responda SOLO con
eso. Sin API key, muestra el prompt que habría enviado — igual se entiende.

Uso:
    ./rag preguntar "¿qué guarda un Control Record?"
"""
import json
import os
import sys
import urllib.error
import urllib.request

try:
    import buscar
except ImportError as e:
    raise SystemExit(
        f"Falta la dependencia '{e.name}': estás usando el Python del sistema,\n"
        "no el del proyecto.\n\n"
        "Usa el lanzador:      ./rag preguntar ...\n"
        "O activa el entorno:  source .venv/bin/activate && export PYTHONPATH=src"
    )

MODELO = "claude-sonnet-5"
API = "https://api.anthropic.com/v1/messages"

PLANTILLA = """Responde la pregunta usando únicamente los fragmentos de abajo.
Si no alcanzan para responder, dilo: no inventes.
Cita el documento del que sacas cada afirmación.

<fragmentos>
{contexto}
</fragmentos>

Pregunta: {pregunta}"""


def armar_prompt(pregunta: str, resultados) -> str:
    contexto = "\n\n".join(
        f"[{c['doc']} · {c['id']}]\n{c['texto']}" for _, c in resultados
    )
    return PLANTILLA.format(contexto=contexto, pregunta=pregunta)


def preguntar_a_claude(prompt: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    cuerpo = json.dumps({
        "model": MODELO,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    pedido = urllib.request.Request(API, data=cuerpo, headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    try:
        with urllib.request.urlopen(pedido, timeout=60) as r:
            return json.load(r)["content"][0]["text"]
    except urllib.error.HTTPError as e:
        return f"[la API respondió {e.code}: {e.read().decode()[:300]}]"
    except (urllib.error.URLError, TimeoutError) as e:
        return f"[no se pudo llamar a la API: {e}]"


def main():
    if len(sys.argv) < 2:
        sys.exit('Uso: python src/preguntar.py "tu pregunta"')
    pregunta = " ".join(sys.argv[1:])

    resultados = buscar.buscar(pregunta)
    print(f"\nPregunta: {pregunta}")
    if not resultados:
        # No llamamos al modelo: sin fragmentos solo podría inventar, y
        # además costaría tokens para nada.
        print("─" * 62)
        print(f"\nNingún fragmento pasa el umbral. El más parecido quedó en "
              f"{buscar.mejor_puntaje(pregunta):.3f}.")
        print("El corpus no cubre esta pregunta, así que no se llama al modelo.\n")
        return

    print("Fragmentos recuperados: " + ", ".join(
        f"{c['id']} ({p:.2f})" for p, c in resultados))
    print("─" * 62)

    prompt = armar_prompt(pregunta, resultados)
    respuesta = preguntar_a_claude(prompt)

    if respuesta is None:
        print("\nSin ANTHROPIC_API_KEY. Este es el prompt que se habría enviado:\n")
        print(prompt)
        print("\n" + "─" * 62)
        print("Ponle la key y vuelve a correr para ver la respuesta generada.")
    else:
        print(f"\n{respuesta}\n")


if __name__ == "__main__":
    main()
