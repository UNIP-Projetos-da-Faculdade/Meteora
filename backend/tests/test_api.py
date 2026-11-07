import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import ConnectionFailure
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app


def test_firmware_post_persists_bson_datetime_and_serializes_id(client, database, payload):
    before = datetime.now(UTC)
    response = client.post("/api/medicoes/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert all(data[key] == value for key, value in payload.items())
    assert len(data["id"]) == 24
    assert "_id" not in data
    document = database.medicoes.find_one()
    assert isinstance(document["timestamp"], datetime)
    assert document["timestamp"].utcoffset() == timedelta(0)
    assert before - timedelta(milliseconds=1) <= document["timestamp"] <= datetime.now(UTC)
    assert data == client.get("/api/medicoes/ultima/").json()


@pytest.mark.parametrize("field", ["temperatura", "umidade", "pressao", "luminosidade"])
def test_all_four_fields_are_required(client, payload, field):
    del payload[field]
    assert client.post("/api/medicoes/", json=payload).status_code == 422


@pytest.mark.parametrize("field", ["temperatura", "umidade", "pressao", "luminosidade"])
@pytest.mark.parametrize("value", [None, True, "27.5", float("nan"), float("inf"), float("-inf")])
def test_rejects_invalid_types_and_nonfinite_values(client, database, payload, field, value):
    payload[field] = value
    response = client.post("/api/medicoes/", content=json.dumps(payload), headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()["detail"]
    assert database.medicoes.count_documents({}) == 0


@pytest.mark.parametrize("patch", [{"umidade": -1}, {"umidade": 101}, {"pressao": -1}, {"luminosidade": -1}, {"timestamp": "2000-01-01T00:00:00Z"}])
def test_rejects_ranges_and_client_timestamp(client, payload, patch):
    assert client.post("/api/medicoes/", json=payload | patch).status_code == 422


def test_rejects_malformed_json_and_nonobject_body(client):
    assert client.post("/api/medicoes/", content='{"temperatura":').status_code == 422
    assert client.post("/api/medicoes/", json=[]).status_code == 422


def test_accepts_zero_and_integer_numbers(client):
    payload = {"temperatura": 0, "umidade": 0, "pressao": 0, "luminosidade": 0}
    assert client.post("/api/medicoes/", json=payload).status_code == 201
    data = client.get("/api/station/latest").json()
    assert data["temperature"] == data["humidity"] == data["pressure"] == data["illuminance"] == 0


def test_history_is_newest_first_and_limited(client, database, payload):
    start = datetime(2026, 11, 6, tzinfo=UTC)
    # Insere fora de ordem para comprovar que a ordenação usa o timestamp.
    for offset in [2, 0, 1]:
        database.medicoes.insert_one(payload | {"temperatura": float(offset), "timestamp": start + timedelta(seconds=offset)})
    data = client.get("/api/medicoes/?limit=2").json()
    assert [item["temperatura"] for item in data] == [2, 1]
    assert client.get("/api/medicoes/ultima/").json() == data[0]


def test_default_history_limit(client, database, payload):
    database.medicoes.insert_many([payload | {"timestamp": datetime.now(UTC)} for _ in range(105)])
    assert len(client.get("/api/medicoes/").json()) == 100


@pytest.mark.parametrize("limit", ["0", "-1", "1001", "1.5", "abc"])
def test_history_limit_validation(client, limit):
    assert client.get(f"/api/medicoes/?limit={limit}").status_code == 422


def test_empty_database(client):
    assert client.get("/api/medicoes/").json() == []
    for path in ["/api/medicoes/ultima/", "/api/station/latest", "/api/forecast"]:
        response = client.get(path)
        assert response.status_code == 204
        assert response.content == b""


def test_station_contract_and_daily_statistics_use_brasilia(client, database, payload):
    # 02:59Z pertence ao dia anterior em Brasília e não deve influenciar os extremos.
    for timestamp, temperature in [("2026-11-06T02:59:00+00:00", -20.0), ("2026-11-06T03:00:00+00:00", 21.0), ("2026-11-07T00:00:00+00:00", 32.0), ("2026-11-07T02:59:00+00:00", 27.5)]:
        database.medicoes.insert_one(payload | {"temperatura": temperature, "timestamp": datetime.fromisoformat(timestamp)})
    data = client.get("/api/station/latest").json()
    assert data == {
        "observedAt": "2026-11-07T02:59:00Z", "temperature": 27.5,
        "humidity": 65.2, "pressure": 1013.25, "illuminance": 350.8,
        "minimum": 21.0, "maximum": 32.0,
        "rain24h": None, "lightRelative": None, "airRaw": None, "feelsLike": None,
    }


def test_health_swagger_and_timestamp_index(client, database):
    assert client.get("/api/health/").json() == {"status": "ok", "database": "ok"}
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/api/medicoes/" in schema["paths"]
    assert database.medicoes.index_information()["medicoes_recentes"]["key"] == [("timestamp", -1), ("_id", -1)]


@pytest.mark.parametrize("method,path,operation", [
    ("post", "/api/medicoes/", "insert_one"),
    ("get", "/api/medicoes/", "find"),
    ("get", "/api/medicoes/ultima/", "find"),
    ("get", "/api/station/latest", "find"),
])
def test_database_unavailability_is_503_without_internal_details(client, database, payload, monkeypatch, method, path, operation):
    client.post("/api/medicoes/", json=payload)

    def unavailable(*args, **kwargs):
        raise ConnectionFailure("mongodb://private-user:private-password@internal-host")

    monkeypatch.setattr(database.medicoes, operation, unavailable)
    response = getattr(client, method)(path, **({"json": payload} if method == "post" else {}))
    assert response.status_code == 503
    assert "private-password" not in response.text
    assert "internal-host" not in response.text


def test_health_reports_database_failure(client, database, monkeypatch):
    def unavailable(*args, **kwargs):
        raise ConnectionFailure("offline")

    monkeypatch.setattr(database, "command", unavailable)
    assert client.get("/api/health/").status_code == 503


def test_database_failure_during_daily_statistics_is_503(client, database, payload, monkeypatch):
    client.post("/api/medicoes/", json=payload)
    original_find = database.medicoes.find
    calls = 0

    def fail_on_statistics(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ConnectionFailure("offline")
        return original_find(*args, **kwargs)

    monkeypatch.setattr(database.medicoes, "find", fail_on_statistics)
    assert client.get("/api/station/latest").status_code == 503


def test_startup_offline_keeps_docs_available_and_recovers(monkeypatch, database, payload):
    original = database.medicoes.create_index

    def unavailable(*args, **kwargs):
        raise ConnectionFailure("offline")

    monkeypatch.setattr(database.medicoes, "create_index", unavailable)
    monkeypatch.setattr("app.main.MongoClient", lambda *args, **kwargs: database.client)
    settings = Settings(_env_file=None, mongodb_database=database.name)
    with TestClient(create_app(settings)) as client:
        assert client.get("/docs").status_code == 200
        assert client.post("/api/medicoes/", json=payload).status_code == 503
        monkeypatch.setattr(database.medicoes, "create_index", original)
        assert client.post("/api/medicoes/", json=payload).status_code == 201
        assert "medicoes_recentes" in database.medicoes.index_information()


def test_cors_allows_only_configured_origins(client):
    headers = {"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type"}
    allowed = client.options("/api/medicoes/", headers=headers)
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    blocked = client.options("/api/medicoes/", headers=headers | {"Origin": "http://other.invalid"})
    assert "access-control-allow-origin" not in blocked.headers


def test_environment_configuration(monkeypatch):
    monkeypatch.setenv("MONGODB_DATABASE", "meteora_custom")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3001, http://127.0.0.1:3001")
    settings = Settings(_env_file=None)
    assert settings.mongodb_database == "meteora_custom"
    assert settings.allowed_origins == ["http://localhost:3001", "http://127.0.0.1:3001"]


def test_database_configuration_is_required(monkeypatch):
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.delenv("MONGODB_DATABASE", raising=False)
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)
    assert {item["loc"] for item in error.value.errors()} == {
        ("mongodb_uri",), ("mongodb_database",),
    }
