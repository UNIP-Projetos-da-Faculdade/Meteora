"""Integração real opcional; usa exclusivamente um banco temporário próprio."""

import os
from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import Settings
from app.main import create_app


@pytest.mark.mongodb
@pytest.mark.skipif(not os.getenv("TEST_MONGODB_URI"), reason="Defina TEST_MONGODB_URI para testar MongoDB real")
def test_round_trip_against_real_mongodb(payload):
    uri = os.environ["TEST_MONGODB_URI"]
    database_name = f"meteora_test_{uuid4().hex}"
    settings = Settings(_env_file=None, mongodb_uri=uri, mongodb_database=database_name)
    with MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=2000) as mongo:
        try:
            collection = mongo[database_name].medicoes
            legacy_id = collection.insert_one(payload.copy()).inserted_id
            with TestClient(create_app(settings)) as client:
                assert client.get("/api/health/").status_code == 200
                assert client.get("/api/medicoes/").json() == []
                assert client.get("/api/medicoes/ultima/").status_code == 204
                assert client.get("/api/station/latest").status_code == 204
                created = client.post("/api/medicoes/", json=payload)
                assert created.status_code == 201
                assert client.get("/api/medicoes/").json() == [created.json()]
                assert client.get("/api/medicoes/ultima/").json() == created.json()
                station = client.get("/api/station/latest").json()
                assert station["illuminance"] == payload["luminosidade"]
                assert station["minimum"] == station["maximum"] == payload["temperatura"]
                document = collection.find_one({"timestamp": {"$exists": True}})
                assert isinstance(document["timestamp"], datetime)
                assert "medicoes_recentes" in collection.index_information()
                collection.delete_one({"_id": document["_id"]})
                assert client.get("/api/medicoes/").json() == []
                assert client.get("/api/medicoes/ultima/").status_code == 204
                assert client.get("/api/station/latest").status_code == 204
                assert collection.count_documents({"_id": legacy_id}) == 1
                assert "timestamp" not in collection.find_one({"_id": legacy_id})
        finally:
            mongo.drop_database(database_name)
