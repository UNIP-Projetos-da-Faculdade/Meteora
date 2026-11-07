"""Valida firmware -> HTTP -> MongoDB -> frontend, sem usar uma placa física."""

import argparse
from datetime import UTC, datetime
from hashlib import sha256
from html import unescape
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
from threading import Thread
import time
from urllib.parse import urlsplit
from uuid import uuid4

from bson import ObjectId
import httpx
from pydantic import ValidationError
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import uvicorn

from app.config import Settings
from app.models import MeasurementIn


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
FRONTEND = ROOT / "frontend"
FIRMWARE = ROOT / "firmware" / "sketch_oct31a" / "sketch_oct31a.ino"
REPORT = BACKEND / ".cache" / "ultima-validacao.json"
EXAMPLE = {"temperatura": 27.5, "umidade": 65.2, "pressao": 1013.25, "luminosidade": 350.8}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def firmware_request() -> tuple[str, str]:
    """Lê nomes, ordem e casas decimais das linhas que montam o JSON no .ino."""
    source = FIRMWARE.read_text(encoding="utf-8")
    fields = re.findall(r'json\s*\+=\s*"\\"(\w+)\\":"\s*\+\s*String\((\w+),\s*(\d+)\)', source)
    require(bool(fields), "Nao foi possivel ler a montagem do JSON do firmware.")
    require({field for field, _, _ in fields} == set(MeasurementIn.model_fields),
            "Os campos do firmware diferem dos campos exigidos pelo backend.")
    require(len(fields) == len(MeasurementIn.model_fields), "Ha campos duplicados no JSON do firmware.")
    require(all(field == variable and field in EXAMPLE for field, variable, _ in fields),
            "As variaveis usadas no JSON do firmware mudaram; revise o contrato.")
    endpoint = re.search(r'const\s+char\s*\*\s*servidor\s*=\s*"([^"]+)"', source)
    require(endpoint is not None, "Nao foi possivel ler a URL do firmware.")
    path = urlsplit(endpoint.group(1)).path
    require(path == "/api/medicoes/", "A rota usada no firmware mudou.")
    require(bool(re.search(r'http\.POST\(\s*json\s*\)', source)), "O firmware nao usa POST do JSON esperado.")
    require(bool(re.search(r'http\.addHeader\(\s*"Content-Type"\s*,\s*"application/json"\s*\)', source)),
            "O firmware nao informa Content-Type application/json.")
    require(bool(re.search(r'resposta\s*==\s*201', source)), "O firmware nao reconhece HTTP 201.")
    require(bool(re.search(r'bmp\.readPressure\(\)\s*/\s*100\.0F', source)),
            "Confira a conversao da pressao para hPa no firmware.")
    body = "{" + ",".join(
        f'"{field}":{EXAMPLE[field]:.{int(places)}f}' for field, _, places in fields
    ) + "}"
    return path, body


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def wait_for_http(client: httpx.Client, url: str, process: subprocess.Popen | None = None) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError("O frontend de validacao encerrou. Confira backend/.cache/validacao-frontend.log.")
        try:
            if client.get(url, timeout=2).status_code == 200:
                return
        except httpx.TransportError:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"O servidor de validacao nao respondeu: {url}")


def run_checks(settings: Settings) -> None:
    environment = os.environ | {
        "MONGODB_URI": settings.mongodb_uri.get_secret_value(),
        "MONGODB_DATABASE": "meteora_test",
        "TEST_MONGODB_URI": settings.mongodb_uri.get_secret_value(),
    }
    node = shutil.which("node")
    require(node is not None, "Node.js nao encontrado. Execute scripts/preparar.cmd.")
    npm = ["cmd.exe", "/d", "/c", "npm.cmd"] if os.name == "nt" else ["npm"]
    commands = [
        ("Dependencias Python", [sys.executable, "-m", "pip", "check"], BACKEND),
        ("Testes backend e MongoDB real", [sys.executable, "-m", "pytest", "-q"], BACKEND),
        ("Testes frontend", [*npm, "test"], FRONTEND),
        ("Lint frontend", [*npm, "run", "lint"], FRONTEND),
        ("TypeScript", [node, "node_modules/typescript/bin/tsc", "--noEmit"], FRONTEND),
        ("Build frontend", [*npm, "run", "build"], FRONTEND),
    ]
    for title, command, directory in commands:
        print(f"\n--- {title} ---", flush=True)
        subprocess.run(command, cwd=directory, env=environment, check=True)


def validate_integration(settings: Settings) -> dict:
    from app.main import create_app

    path, body = firmware_request()
    firmware_hash = sha256(FIRMWARE.read_bytes()).hexdigest()
    node = shutil.which("node")
    require(node is not None, "Node.js nao encontrado.")
    require((FRONTEND / ".next" / "BUILD_ID").is_file(),
            "Build do frontend ausente. Execute scripts/validar.cmd sem --somente-integracao.")
    database_name = f"meteora_test_{uuid4().hex}"
    test_settings = settings.model_copy(update={"mongodb_database": database_name})
    server = uvicorn.Server(uvicorn.Config(
        create_app(test_settings), host="127.0.0.1", port=free_port(), log_level="warning",
    ))
    api_url = f"http://127.0.0.1:{server.config.port}"
    thread = Thread(target=server.run, daemon=True)
    frontend_process = None
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with MongoClient(
        settings.mongodb_uri.get_secret_value(), tz_aware=True,
        serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
    ) as mongo, httpx.Client(timeout=10, trust_env=False) as client, (
        REPORT.parent / "validacao-frontend.log"
    ).open("w", encoding="utf-8") as frontend_log:
        mongo.admin.command("ping")
        require(database_name not in mongo.list_database_names(), "O banco temporario ja existe.")
        try:
            thread.start()
            wait_for_http(client, f"{api_url}/api/health/")
            frontend_url = f"http://127.0.0.1:{free_port()}"
            environment = os.environ | {
                "METEORA_STATION_URL": f"{api_url}/api/station/latest",
                "METEORA_FORECAST_URL": "",
                "METEORA_API_TOKEN": "",
            }
            frontend_process = subprocess.Popen(
                [node, str(FRONTEND / "node_modules/next/dist/bin/next"), "start",
                 "--hostname", "127.0.0.1", "--port", str(urlsplit(frontend_url).port)],
                cwd=FRONTEND, env=environment, stdout=frontend_log, stderr=subprocess.STDOUT,
                **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
            )
            wait_for_http(client, f"{frontend_url}/api/meteora", frontend_process)
            collection = mongo[database_name].medicoes
            legacy_id = collection.insert_one(EXAMPLE.copy()).inserted_id
            require(client.get(f"{api_url}/api/station/latest").status_code == 204,
                    "Um registro sem timestamp foi aceito como leitura valida.")
            require(client.get(f"{api_url}/docs").status_code == 200, "Swagger indisponivel.")

            created = client.post(f"{api_url}{path}", content=body, headers={"Content-Type": "application/json"})
            require(created.status_code == 201, f"POST do firmware retornou HTTP {created.status_code}.")
            measurement = created.json()
            document = collection.find_one({"_id": ObjectId(measurement["id"])})
            require(document is not None, "O MongoDB nao armazenou a medicao.")
            require(all(document[key] == value for key, value in EXAMPLE.items()), "Valores alterados na gravacao.")
            require(isinstance(document["timestamp"], datetime), "Timestamp nao foi armazenado como data BSON.")
            require(document["timestamp"].utcoffset().total_seconds() == 0, "O timestamp nao esta em UTC.")
            require("medicoes_recentes" in collection.index_information(), "Indice de timestamp ausente.")
            require(client.get(f"{api_url}/api/medicoes/ultima/").json() == measurement, "Ultima medicao incorreta.")
            require(client.get(f"{api_url}/api/medicoes/?limit=1").json() == [measurement], "Historico incorreto.")

            dashboard = client.get(f"{frontend_url}/api/meteora").json()
            require(dashboard["station"]["status"] == "ready", "O frontend rejeitou a resposta da API.")
            reading = dashboard["station"]["data"]
            for key, alias in {
                "temperatura": "temperature", "umidade": "humidity",
                "pressao": "pressure", "luminosidade": "illuminance",
            }.items():
                require(reading[alias] == EXAMPLE[key], f"O frontend recebeu um valor incorreto para {key}.")
            require(reading["observedAt"] == measurement["timestamp"], "Horario alterado na integracao do frontend.")
            require(reading["minimum"] == reading["maximum"] == EXAMPLE["temperatura"], "Extremos incorretos.")
            html = client.get(frontend_url).raise_for_status().text
            visible = unescape(re.sub(r"<[^>]+>", " ", re.sub(
                r"<(script|style)\b.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE,
            )))
            require(all(label in visible for label in ["Temperatura", "Umidade", "Pressão", "Luminosidade"]),
                    "A pagina nao apresenta as quatro medicoes.")
            require(all(label not in visible for label in ["Chuva", "Previsão por hora", "Próximos 7 dias", "Sensor de ar"]),
                    "A pagina ainda apresenta secoes fora do escopo dos sensores.")

            failed_sensor = EXAMPLE | {"luminosidade": -1.0}
            accepted = client.post(f"{api_url}{path}", json=failed_sensor)
            require(accepted.status_code == 201, "A falha do BH1750 descartou a medicao inteira.")
            failed_measurement = accepted.json()
            failed_document = collection.find_one({"_id": ObjectId(failed_measurement["id"])})
            require(failed_document is not None and all(
                failed_document[key] == value for key, value in failed_sensor.items()
            ), "Os valores com falha do sensor nao foram preservados no MongoDB.")
            require(client.get(f"{api_url}/api/medicoes/ultima/").json() == failed_measurement,
                    "O historico nao preservou a falha numerica do sensor.")
            partial = client.get(f"{frontend_url}/api/meteora").json()["station"]
            require(partial["status"] == "ready" and partial["data"]["illuminance"] is None,
                    "O frontend nao isolou a falha de luminosidade.")
            for field, alias in {
                "temperatura": "temperature", "umidade": "humidity", "pressao": "pressure",
            }.items():
                require(partial["data"][alias] == EXAMPLE[field],
                        f"A falha do BH1750 descartou a leitura de {field}.")

            collection.delete_one({"_id": failed_document["_id"]})
            collection.delete_one({"_id": document["_id"]})
            require(client.get(f"{api_url}/api/medicoes/").json() == [], "Historico vazio incorreto.")
            require(client.get(f"{api_url}/api/station/latest").status_code == 204, "A limpeza causou erro na ultima leitura.")
            require(client.get(f"{frontend_url}/api/meteora").json()["station"]["data"] is None,
                    "O frontend nao reconheceu a ausencia de leitura depois da limpeza.")
            require(collection.count_documents({"_id": legacy_id}) == 1, "O registro antigo foi alterado.")
            require(sha256(FIRMWARE.read_bytes()).hexdigest() == firmware_hash, "O firmware foi alterado na validacao.")
            return {
                "status": "ok", "timestamp": datetime.now(UTC).isoformat(),
                "firmware_sha256": firmware_hash, "payload_firmware": json.loads(body),
                "checks": ["contrato_firmware", "post_201", "mongo_bson_utc", "indice_timestamp",
                           "historico", "ultima_medicao", "frontend_quatro_campos", "pagina",
                           "falha_bh1750_preserva_outros_sensores",
                           "registro_sem_timestamp", "retorno_204_apos_limpeza"],
                "hardware_tested": False,
            }
        finally:
            try:
                if frontend_process is not None and frontend_process.poll() is None:
                    frontend_process.terminate()
                    frontend_process.wait(timeout=10)
            finally:
                server.should_exit = True
                try:
                    if thread.ident is not None:
                        thread.join(timeout=10)
                    require(not thread.is_alive(), "O servidor temporario nao encerrou.")
                finally:
                    # Nome gerado para esta execução; nunca remove o banco do .env.
                    mongo.drop_database(database_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--somente-integracao", action="store_true", help="Usa o build existente e pula os testes/lint/build.")
    args = parser.parse_args()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"status": "running", "hardware_tested": False}), encoding="utf-8")
    try:
        settings = Settings()
        if not args.somente_integracao:
            run_checks(settings)
        print("\n--- Integracao real com payload extraido do firmware ---", flush=True)
        result = validate_integration(settings)
        result["automated_checks_run"] = not args.somente_integracao
        REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("OK: JSON do firmware -> POST 201 -> MongoDB -> API -> frontend.", flush=True)
        print("Banco e servidores temporarios encerrados. Dados do projeto preservados.", flush=True)
        print("Relatorio: backend/.cache/ultima-validacao.json", flush=True)
        print("A validacao nao usa USB e nao testa sensores, Wi-Fi ou firewall do ESP32.", flush=True)
        return 0
    except (ValidationError, PyMongoError):
        message = "Confira backend/.env e se o MongoDB esta em execucao."
    except subprocess.CalledProcessError:
        message = "Uma das verificacoes falhou. Confira a etapa e a mensagem acima."
    except (RuntimeError, OSError, ValueError, KeyError, httpx.HTTPError) as error:
        message = str(error)
    REPORT.write_text(json.dumps({"status": "failed", "hardware_tested": False}), encoding="utf-8")
    print(f"FALHA: {message}", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
