# RAG sobre Floci

Un RAG mínimo que corre hoy en esta máquina sin Docker, y que migra a
[Floci](https://github.com/floci-io/floci) —emulador local de AWS— cambiando
una variable de entorno.

## Las dos guías

| Hoja | Qué cubre |
|---|---|
| [`guia.html`](guia.html) | **Empieza aquí.** Uso del RAG: indexar, buscar, preguntar. Qué hace cada archivo y las decisiones de diseño. |
| [`floci.html`](floci.html) | Paso siguiente: apuntar el almacén a S3 y DynamoDB emulados con Floci. |

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
./rag ingest                                      # indexa ./docs
./rag buscar     "¿qué guarda un Control Record?"
./rag preguntar  "¿qué es un Behavior Qualifier?"
```

El lanzador `./rag` usa `.venv/bin/python` y arma `PYTHONPATH`: corre desde
cualquier directorio sin activar el entorno. Si invocas los scripts a mano con
el Python del sistema, te dicen qué hacer en vez de tirar un traceback.

Para la generación, exporta `ANTHROPIC_API_KEY`. Sin ella, `preguntar.py` te
muestra el prompt que habría enviado.

## Pasar a Floci

Paso a paso completo en [`floci.html`](floci.html). El resumen:

```bash
curl -fsSL https://floci.io/install.sh | sh     # CLI
floci start                                      # necesita Docker corriendo

export RAG_BACKEND=floci
./rag ingest                                     # crea bucket y tabla solos
```

## Huella

Medido en CPU, sin GPU.

| Qué | Cuánto |
|---|---|
| `.venv` | 210 MB — fastembed usa onnxruntime, no torch |
| Modelo de embeddings | 241 MB en `~/.cache/fastembed` |
| Carga del modelo | ~20 s la primera vez, ~1 s después |
| Vectorizar | ~7 ms por fragmento |
| Imagen de Floci | 90 MB · ~13 MB idle |

## Decisiones que vale la pena conocer

**El vector va a DynamoDB como binario, no como lista de números.** 384 floats
son 1.5 KB en `tobytes()`, y DynamoDB no tiene tipo float nativo: la
alternativa era convertir cada número a `Decimal`.

**Hay un umbral de relevancia, no un `k` fijo.** `MINIMO = 0.40` en
`config.py`. Sin ese corte, pedir 4 fragmentos siempre devuelve 4, aunque tres
no hablen del tema: eso diluye la señal, multiplica los tokens y le da al
modelo material para mezclar conceptos. Si nada pasa el umbral, `preguntar.py`
**no llama al modelo** — sin fragmentos solo podría inventar.

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

- Un conjunto de preguntas con su respuesta esperada. Es lo primero: sin eso,
  mover `CHUNK` o `MINIMO` es a ciegas.
- Calibrar `MINIMO` con esos datos. El 0.40 salió a ojo.
- Reindexar solo lo que cambió, en vez de todo (`ingest.py` reescribe siempre).
- Reranking: traer 20 fragmentos y reordenarlos antes de armar el prompt. Eso
  arregla el caso del fragmento vecino, que el umbral no resuelve.
