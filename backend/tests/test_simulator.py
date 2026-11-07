import json
import sys
from urllib.error import URLError

import pytest

from app.config import Settings
from scripts import simular_esp32


def test_simulation_uses_api_and_cleanup_preserves_other_measurements(
    client, database, payload, monkeypatch, tmp_path
):
    existing = client.post("/api/medicoes/", json=payload).json()
    settings = Settings(_env_file=None, mongodb_database=database.name)
    monkeypatch.setattr(simular_esp32, "SIMULATIONS", tmp_path)
    sent = []

    def send(api_url, data):
        sent.append(data)
        response = client.post("/api/medicoes/", json=data)
        assert response.status_code == 201
        return response.json()["id"]

    monkeypatch.setattr(simular_esp32, "send_measurement", send)
    monkeypatch.setattr(simular_esp32, "MongoClient", lambda *a, **kw: database.client)
    assert simular_esp32.simulate(settings, "http://127.0.0.1:8000", 3, 0.001) == 0
    assert len(sent) == 3
    assert database.medicoes.count_documents({}) == 4
    manifest = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert len(manifest["ids"]) == 3
    assert "MONGODB_URI" not in manifest
    assert settings.mongodb_uri.get_secret_value() not in json.dumps(manifest)

    assert simular_esp32.clean_simulations(settings, "http://127.0.0.1:8000") == 0
    assert database.medicoes.count_documents({}) == 1
    assert client.get("/api/medicoes/ultima/").json() == existing
    assert not list(tmp_path.glob("*.json"))


@pytest.mark.parametrize("patch", [{"database": "outro_banco"}, {"connection": "outra_conexao"}, {"api_url": "http://localhost:9999"}])
def test_cleanup_ignores_manifests_from_other_configurations(
    client, database, payload, monkeypatch, tmp_path, patch
):
    reading = client.post("/api/medicoes/", json=payload).json()
    settings = Settings(_env_file=None, mongodb_database=database.name)
    manifest = {
        "database": settings.mongodb_database,
        "connection": simular_esp32.connection_fingerprint(settings),
        "api_url": "http://127.0.0.1:8000",
        "ids": [reading["id"]],
    } | patch
    (tmp_path / "other.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(simular_esp32, "SIMULATIONS", tmp_path)
    monkeypatch.setattr(simular_esp32, "MongoClient", lambda *a, **kw: database.client)
    simular_esp32.clean_simulations(settings, "http://127.0.0.1:8000")
    assert database.medicoes.count_documents({}) == 1
    assert (tmp_path / "other.json").exists()


def test_simulator_explains_when_backend_is_not_running(monkeypatch, capsys):
    def unavailable(*args):
        raise URLError("connection refused")

    monkeypatch.setattr(simular_esp32, "simulate", unavailable)
    monkeypatch.setattr(sys, "argv", ["simular_esp32", "--count", "1"])
    assert simular_esp32.main() == 1
    assert "Inicie iniciar-backend.cmd" in capsys.readouterr().out


@pytest.mark.parametrize("interval", ["0", "-1", "nan", "inf"])
def test_simulator_rejects_invalid_intervals(monkeypatch, interval):
    monkeypatch.setattr(sys, "argv", ["simular_esp32", f"--interval={interval}"])
    with pytest.raises(SystemExit) as error:
        simular_esp32.main()
    assert error.value.code == 2
