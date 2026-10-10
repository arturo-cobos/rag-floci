# RAG sobre Floci

Un RAG mínimo que corre hoy en esta máquina sin Docker, y que migra a
[Floci](https://github.com/floci-io/floci) —emulador local de AWS— cambiando
una variable de entorno.

## Lo primero: Floci no es una herramienta de RAG

Floci es la alternativa libre a LocalStack: te da S3, DynamoDB, Lambda y 60+
servicios AWS en `localhost:4566`, sin cuenta ni token. Sirve para montar un
RAG *con forma de AWS* y probarlo sin gastar, pero el RAG lo escribes tú.

**Floci necesita Docker o Podman.** El CLI se instala sin él, pero `floci start`
arranca un contenedor y monta `/var/run/docker.sock`.

## Arquitectura

| Pieza | Con `local` | Con `floci` |
|---|---|---|
| Documentos | archivos en `almacen/docs/` | **S3** (bucket `rag-docs`) |
| Fragmentos + vectores | `chunks.jsonl` + `vectores.npy` | **DynamoDB** (tabla `rag-chunks`) |
| Búsqueda | coseno en numpy | coseno en numpy |
| Embeddings | fastembed en CPU, 384 dims | igual |
| Generación | Claude API (opcional) | igual |

El código no sabe cuál está usando: `src/store.py` tiene las dos
implementaciones detrás de una sola interfaz.

## Correr

```bash
source .venv/bin/activate
export PYTHONPATH=src

python src/ingest.py                              # indexa ./docs
python src/buscar.py "¿qué guarda un Control Record?"
python src/preguntar.py "¿qué es un Behavior Qualifier?"
```

Para la generación, exporta `ANTHROPIC_API_KEY`. Sin ella, `preguntar.py` te
muestra el prompt que habría enviado.

## Pasar a Floci

```bash
curl -fsSL https://floci.io/install.sh | sh     # CLI (hay binario linux-arm64)
floci start                                      # necesita Docker corriendo

export RAG_BACKEND=floci
python src/ingest.py                             # crea bucket y tabla solos
```

## Recursos medidos en esta máquina

aarch64, 8 cores, 7.7 GB RAM, sin GPU.

| Qué | Cuánto |
|---|---|
| `.venv` | 210 MB (sin torch: fastembed usa onnxruntime) |
| Modelo de embeddings | 241 MB en `~/.cache/fastembed` |
| Carga del modelo | ~20 s la primera vez, ~1 s después |
| Vectorizar | ~7 ms por fragmento en CPU |
| Imagen de Floci | 90 MB · ~13 MB idle |

## Decisiones que vale la pena conocer

**El vector va a DynamoDB como binario, no como lista de números.** 384 floats
son 1.5 KB en `tobytes()`, y DynamoDB no tiene tipo float nativo: la
alternativa era convertir cada número a `Decimal`.

**La búsqueda es fuerza bruta a propósito.** Comparar contra todos es exacto y
tarda milisegundos hasta decenas de miles de fragmentos. Un índice aproximado
(el k-NN de OpenSearch) solo paga por encima de eso, y en Floci OpenSearch
levanta un contenedor aparte de ~1.5 GB.

**Los fragmentos se parten por párrafos, no por número de caracteres.** Cortar
a mitad de frase es lo que más daña la calidad de la recuperación. El solape de
150 caracteres le da contexto al fragmento siguiente.

**El modelo de embeddings es multilingüe.** Uno entrenado solo en inglés no
falla sobre texto en español: simplemente recupera fragmentos mediocres, que es
un síntoma mucho más difícil de diagnosticar.

## Lo que falta antes de usarlo en serio

- Reindexar solo lo que cambió, en vez de todo (`ingest.py` reescribe siempre).
- Un conjunto de preguntas con su respuesta esperada, para medir si un cambio
  de tamaño de fragmento mejora o empeora.
- Reranking: traer 20 fragmentos y reordenarlos antes de armar el prompt.
