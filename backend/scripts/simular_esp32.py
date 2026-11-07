"""Envia o JSON do firmware e registra os ids para limpar apenas a simulação."""

import argparse
from datetime import UTC, datetime
from hashlib import sha256
import json
import math
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4

from bson import ObjectId
from pydantic import ValidationError
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import Settings


SIMULATIONS = Path(__file__).resolve().parents[1] / ".cache" / "simulacoes"


def sensor_payload(sequence: int) -> dict[str, float]:
    return {
        "temperatura": round(26 + 3 * math.sin(sequence / 4), 2),
        "umidade": round(65 + 8 * math.cos(sequence / 5), 2),
        "pressao": round(1013 + 2 * math.sin(sequence / 6), 2),
        "luminosidade": round(350 + 200 * math.sin(sequence / 3), 2),
    }


def connection_fingerprint(settings: Settings) -> str:
    # O diário local não precisa guardar a URI nem eventuais credenciais.
    return sha256(settings.mongodb_uri.get_secret_value().encode()).hexdigest()


def save_manifest(path: Path, manifest: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temporary.replace(path)


def send_measurement(api_url: str, payload: dict[str, float]) -> str:
    request = Request(
        f"{api_url.rstrip('/')}/api/medicoes/",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=8) as response:
        if response.status != 201:
            raise ValueError("A API nao retornou HTTP 201.")
        identifier = json.load(response)["id"]
        if not ObjectId.is_valid(identifier):
            raise ValueError("A API retornou um identificador invalido.")
        return identifier


def simulate(settings: Settings, api_url: str, count: int, interval: float) -> int:
    SIMULATIONS.mkdir(parents=True, exist_ok=True)
    path = SIMULATIONS / f"{uuid4().hex}.json"
    manifest = {
        "database": settings.mongodb_database,
        "connection": connection_fingerprint(settings),
        "api_url": api_url,
        "started_at": datetime.now(UTC).isoformat(),
        "ids": [],
    }
    print("SIMULACAO: valores ficticios enviados pelo mesmo endpoint do ESP32.", flush=True)
    print(f"Banco configurado: {settings.mongodb_database}; colecao: medicoes.", flush=True)
    print("A API deve usar esse mesmo .env. Pare com Ctrl+C antes de usar sensores reais.", flush=True)
    sequence = 0
    try:
        while count == 0 or sequence < count:
            payload = sensor_payload(sequence)
            identifier = send_measurement(api_url, payload)
            manifest["ids"].append(identifier)
            save_manifest(path, manifest)
            sequence += 1
            print(f"HTTP 201 | id={identifier} | {json.dumps(payload)}", flush=True)
            if count == 0 or sequence < count:
                time.sleep(interval)
    except KeyboardInterrupt:
        print("\nSimulacao encerrada.", flush=True)
    finally:
        if manifest["ids"]:
            print("Os dados ficam no MongoDB. Use limpar-dados-simulados.cmd para remover so estes testes.", flush=True)
    return 0


def clean_simulations(settings: Settings, api_url: str) -> int:
    # A limpeza usa a conexão local do .env e só ids registrados pelo simulador.
    if urlsplit(api_url).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Execute a limpeza no computador do backend, usando a URL local.")
    removed = 0
    with MongoClient(
        settings.mongodb_uri.get_secret_value(),
        serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
    ) as client:
        collection = client[settings.mongodb_database].medicoes
        for path in SIMULATIONS.glob("*.json"):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if (
                manifest["database"] != settings.mongodb_database
                or manifest["connection"] != connection_fingerprint(settings)
                or manifest["api_url"] != api_url
            ):
                continue
            identifiers = [ObjectId(value) for value in manifest["ids"]]
            removed += collection.delete_many({"_id": {"$in": identifiers}}).deleted_count
            path.unlink()
    print(f"Removidas {removed} medicoes simuladas. Outros registros foram preservados.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=0, help="Quantidade; 0 envia ate Ctrl+C (padrao).")
    parser.add_argument("--interval", type=float, default=10, help="Segundos entre envios; padrao 10.")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Endereco base da API.")
    parser.add_argument("--limpar", action="store_true", help="Remove somente ids registrados pelas simulacoes locais.")
    args = parser.parse_args()
    if args.count < 0 or not math.isfinite(args.interval) or args.interval <= 0:
        parser.error("Use --count >= 0 e --interval positivo e finito.")
    endpoint = urlsplit(args.url)
    if endpoint.scheme not in {"http", "https"} or not endpoint.hostname or endpoint.username:
        parser.error("Use uma URL HTTP/HTTPS sem credenciais.")
    # Não misturar diários de testes enviados a outra máquina com a limpeza local.
    if not args.limpar and endpoint.hostname not in {"localhost", "127.0.0.1", "::1"}:
        parser.error("Execute o simulador no computador do backend, usando localhost ou 127.0.0.1.")
    try:
        settings = Settings()
        if args.limpar:
            return clean_simulations(settings, args.url)
        return simulate(settings, args.url, args.count, args.interval)
    except ValidationError:
        print("Confira MONGODB_URI e MONGODB_DATABASE em backend/.env.")
    except HTTPError as error:
        print(f"A API retornou HTTP {error.code}. Confira a janela do backend e /api/health/.")
    except (URLError, TimeoutError, ConnectionError):
        print("Nao foi possivel acessar a API. Inicie iniciar-backend.cmd e tente novamente.")
    except PyMongoError:
        print("Nao foi possivel acessar o MongoDB. Confira o servico e backend/.env.")
    except (ValueError, KeyError, OSError):
        print("Nao foi possivel concluir a operacao. Confira a API e os arquivos em backend/.cache/simulacoes.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
