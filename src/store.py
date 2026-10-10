"""El almacén. Dos implementaciones, una sola interfaz.

`LocalStore` escribe archivos. `AwsStore` habla S3 + DynamoDB con boto3,
apuntando a Floci. El resto del proyecto no distingue cuál está usando: por eso
puedes empezar sin Docker y migrar a Floci cambiando una variable.
"""
import json
import pathlib

import numpy as np

import config

ALMACEN = pathlib.Path(__file__).parent.parent / "almacen"


class LocalStore:
    """Archivos planos. Cero dependencias, cero servicios."""

    nombre = "local (archivos en ./almacen)"

    def __init__(self):
        (ALMACEN / "docs").mkdir(parents=True, exist_ok=True)

    def guardar_documento(self, nombre: str, texto: str) -> None:
        (ALMACEN / "docs" / nombre).write_text(texto)

    def guardar_chunks(self, chunks: list[dict], vectores: np.ndarray) -> None:
        (ALMACEN / "chunks.jsonl").write_text(
            "\n".join(json.dumps(c, ensure_ascii=False) for c in chunks)
        )
        np.save(ALMACEN / "vectores.npy", vectores)

    def leer_chunks(self) -> tuple[list[dict], np.ndarray]:
        ruta = ALMACEN / "chunks.jsonl"
        if not ruta.exists():
            return [], np.zeros((0, config.DIMS), dtype=np.float32)
        chunks = [json.loads(l) for l in ruta.read_text().splitlines() if l]
        return chunks, np.load(ALMACEN / "vectores.npy")


class AwsStore:
    """S3 para los documentos, DynamoDB para los fragmentos y sus vectores.

    Con Floci corriendo esto es AWS de verdad en la forma: los mismos llamados
    de boto3 funcionan contra la nube real cambiando solo el endpoint.
    """

    nombre = f"floci ({config.ENDPOINT})"

    def __init__(self):
        import boto3

        comun = dict(
            endpoint_url=config.ENDPOINT,
            region_name=config.REGION,
            # Floci no valida credenciales, pero boto3 exige que existan.
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
        self.s3 = boto3.client("s3", **comun)
        self.ddb = boto3.client("dynamodb", **comun)
        self._crear_si_falta()

    def _crear_si_falta(self) -> None:
        buckets = [b["Name"] for b in self.s3.list_buckets().get("Buckets", [])]
        if config.BUCKET not in buckets:
            self.s3.create_bucket(Bucket=config.BUCKET)

        if config.TABLA not in self.ddb.list_tables().get("TableNames", []):
            self.ddb.create_table(
                TableName=config.TABLA,
                KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )
            self.ddb.get_waiter("table_exists").wait(TableName=config.TABLA)

    def guardar_documento(self, nombre: str, texto: str) -> None:
        self.s3.put_object(Bucket=config.BUCKET, Key=nombre, Body=texto.encode())

    def guardar_chunks(self, chunks: list[dict], vectores: np.ndarray) -> None:
        for c, v in zip(chunks, vectores):
            self.ddb.put_item(
                TableName=config.TABLA,
                Item={
                    "id": {"S": c["id"]},
                    "doc": {"S": c["doc"]},
                    "texto": {"S": c["texto"]},
                    # El vector va como binario, no como lista de números:
                    # 384 floats son 1.5 KB así, y DynamoDB no maneja float
                    # nativo (tocaría convertir todo a Decimal).
                    "vector": {"B": v.astype(np.float32).tobytes()},
                },
            )

    def leer_chunks(self) -> tuple[list[dict], np.ndarray]:
        chunks, vectores, arranque = [], [], None
        while True:
            kw = {"TableName": config.TABLA}
            if arranque:
                kw["ExclusiveStartKey"] = arranque
            r = self.ddb.scan(**kw)
            for it in r.get("Items", []):
                chunks.append({
                    "id": it["id"]["S"],
                    "doc": it["doc"]["S"],
                    "texto": it["texto"]["S"],
                })
                vectores.append(np.frombuffer(it["vector"]["B"], dtype=np.float32))
            arranque = r.get("LastEvaluatedKey")
            if not arranque:
                break
        if not chunks:
            return [], np.zeros((0, config.DIMS), dtype=np.float32)
        return chunks, np.vstack(vectores)


def abrir():
    """Devuelve el almacén que toque según RAG_BACKEND."""
    if config.BACKEND == "floci":
        return AwsStore()
    if config.BACKEND == "local":
        return LocalStore()
    raise SystemExit(f"RAG_BACKEND desconocido: {config.BACKEND!r} (usa local o floci)")
