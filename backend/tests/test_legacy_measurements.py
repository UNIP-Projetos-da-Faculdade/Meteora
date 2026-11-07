from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.parametrize("timestamp", [None, "2026-11-07T12:00:00Z", 1794052800, []])
def test_incompatible_timestamp_does_not_crash_or_change_existing_documents(
    client, database, payload, timestamp
):
    # Reproduz o registro manual sem timestamp que causava KeyError no dashboard.
    database.medicoes.insert_one(payload.copy())
    database.medicoes.insert_one(payload | {"timestamp": timestamp})
    assert client.get("/api/medicoes/").json() == []
    for endpoint in ["/api/medicoes/ultima/", "/api/station/latest"]:
        response = client.get(endpoint)
        assert response.status_code == 204
        assert response.content == b""
    assert database.medicoes.count_documents({}) == 2
    assert database.medicoes.count_documents({"timestamp": {"$exists": False}}) == 1


def test_reads_ignore_legacy_records_before_and_after_new_measurements(client, database, payload):
    legacy_id = database.medicoes.insert_one(payload.copy()).inserted_id
    created = client.post("/api/medicoes/", json=payload).json()
    assert client.get("/api/medicoes/?limit=1").json() == [created]
    assert client.get("/api/medicoes/ultima/").json() == created
    assert client.get("/api/station/latest").json()["temperature"] == payload["temperatura"]

    # Reproduz também a volta ao registro antigo depois de limpar a simulação.
    database.medicoes.delete_many({"_id": {"$ne": legacy_id}})
    assert client.get("/api/medicoes/").json() == []
    assert client.get("/api/medicoes/ultima/").status_code == 204
    assert client.get("/api/station/latest").status_code == 204
    assert "timestamp" not in database.medicoes.find_one({"_id": legacy_id})


@pytest.mark.parametrize("patch", [
    {"temperatura": None}, {"umidade": None}, {"pressao": "1013 hPa"},
    {"luminosidade": "350 lux"}, {"temperatura": float("nan")},
    {"luminosidade": float("inf")}, {"umidade": [50]},
    {"timestamp": [datetime(2026, 11, 7, 12, tzinfo=UTC)]},
])
def test_incompatible_newer_documents_do_not_hide_valid_readings(
    client, database, payload, patch
):
    valid = client.post("/api/medicoes/", json=payload).json()
    database.medicoes.insert_one(payload | {"timestamp": datetime.now(UTC) + timedelta(hours=1)} | patch)
    assert client.get("/api/medicoes/?limit=1").json() == [valid]
    assert client.get("/api/medicoes/ultima/").json() == valid
    assert client.get("/api/station/latest").json()["temperature"] == payload["temperatura"]
    assert database.medicoes.count_documents({}) == 2


def test_daily_extremes_ignore_invalid_records_from_same_day(client, database, payload):
    observed_at = datetime(2026, 11, 7, 12, tzinfo=UTC)
    database.medicoes.insert_one(payload | {"temperatura": 25.0, "timestamp": observed_at})
    for patch in [{"temperatura": -200.0, "umidade": None}, {"temperatura": 200.0, "pressao": None}]:
        database.medicoes.insert_one(payload | {"timestamp": observed_at - timedelta(minutes=1)} | patch)
    data = client.get("/api/station/latest").json()
    assert data["minimum"] == data["maximum"] == 25.0
    assert database.medicoes.count_documents({}) == 3
