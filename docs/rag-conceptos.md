# Cómo funciona un RAG

RAG significa Retrieval-Augmented Generation. La idea es simple: en vez de
esperar que el modelo de lenguaje se acuerde de tus documentos, se los pasas en
el momento de preguntar. El modelo no aprende nada nuevo; solo lee lo que le
pones delante.

## Los tres pasos

La ingesta parte los documentos en fragmentos y convierte cada uno en un vector
mediante un modelo de embeddings. Ese vector es una lista de números que captura
el significado del texto: dos fragmentos que dicen cosas parecidas quedan cerca
en el espacio vectorial, aunque no compartan ni una palabra.

La recuperación convierte la pregunta en un vector con el mismo modelo y busca
los fragmentos más cercanos. La medida habitual es la similitud coseno, que
compara la dirección de los vectores e ignora su magnitud.

La generación arma un prompt con los fragmentos recuperados y la pregunta, y le
pide al modelo que responda usando solo eso. Esa restricción es la que reduce
las alucinaciones: el modelo tiene de dónde citar.

## Dónde se rompe

El tamaño del fragmento es el parámetro que más impacta. Fragmentos muy cortos
pierden contexto y fragmentos muy largos diluyen la señal: el vector promedia
demasiados temas y deja de parecerse a ninguna pregunta en particular.

El modelo de embeddings tiene que cubrir el idioma de los documentos. Un modelo
entrenado solo en inglés da resultados malos sobre texto en español, y el
síntoma es confuso: no falla, simplemente recupera fragmentos mediocres.

La búsqueda por fuerza bruta compara contra todos los vectores. Es exacta y
rápida hasta decenas de miles de fragmentos. Por encima de eso conviene un
índice aproximado, que gana velocidad a cambio de perder algunos resultados.
