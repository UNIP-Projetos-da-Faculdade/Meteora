import json

from scripts.validar_integracao import EXAMPLE, firmware_request


def test_exact_json_assembled_by_firmware_is_accepted_and_reaches_dashboard(client, database):
    path, body = firmware_request()
    assert json.loads(body) == EXAMPLE
    response = client.post(path, content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == 201
    assert all(response.json()[key] == value for key, value in EXAMPLE.items())
    reading = client.get("/api/station/latest").json()
    assert reading["temperature"] == EXAMPLE["temperatura"]
    assert reading["humidity"] == EXAMPLE["umidade"]
    assert reading["pressure"] == EXAMPLE["pressao"]
    assert reading["illuminance"] == EXAMPLE["luminosidade"]
    assert database.medicoes.count_documents({}) == 1
