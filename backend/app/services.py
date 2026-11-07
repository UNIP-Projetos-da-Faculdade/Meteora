from collections.abc import Iterator
from datetime import UTC, datetime, time, timedelta
from itertools import islice
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import ValidationError
from pymongo import DESCENDING
from pymongo.collection import Collection

from app.models import MeasurementIn, MeasurementOut, StationReading


RECENT_FIRST = [("timestamp", DESCENDING), ("_id", DESCENDING)]
STATION_TIME_ZONE = ZoneInfo("America/Sao_Paulo")


def measurement_response(document: dict[str, Any]) -> MeasurementOut:
    return MeasurementOut(
        id=str(document["_id"]),
        **{key: document.get(key) for key in (*MeasurementIn.model_fields, "timestamp")},
    )


def valid_measurements(
    collection: Collection[dict[str, Any]],
    timestamp_filter: dict[str, Any] | None = None,
) -> Iterator[MeasurementOut]:
    """Documentos antigos/manuais podem não seguir o contrato de ingestão."""
    query = {"timestamp": {"$type": "date", **(timestamp_filter or {})}}
    with collection.find(query).sort(RECENT_FIRST) as documents:
        for document in documents:
            try:
                measurement = measurement_response(document)
            except ValidationError:
                continue
            yield measurement


def create_measurement(
    collection: Collection[dict[str, Any]], measurement: MeasurementIn
) -> MeasurementOut:
    now = datetime.now(UTC)
    # BSON tem precisão de milissegundos: POST e GET devem retornar o mesmo instante.
    document = measurement.model_dump() | {
        "timestamp": now.replace(microsecond=now.microsecond // 1000 * 1000)
    }
    result = collection.insert_one(document)
    document["_id"] = result.inserted_id
    return measurement_response(document)


def list_measurements(
    collection: Collection[dict[str, Any]], limit: int
) -> list[MeasurementOut]:
    return list(islice(valid_measurements(collection), limit))


def latest_measurement(collection: Collection[dict[str, Any]]) -> MeasurementOut | None:
    return next(valid_measurements(collection), None)


def station_reading(
    collection: Collection[dict[str, Any]], latest: MeasurementOut
) -> StationReading:
    observed_at = latest.timestamp
    local_day = observed_at.astimezone(STATION_TIME_ZONE).date()
    start = datetime.combine(local_day, time.min, STATION_TIME_ZONE).astimezone(UTC)
    end = datetime.combine(
        local_day + timedelta(days=1), time.min, STATION_TIME_ZONE
    ).astimezone(UTC)
    minimum = maximum = latest.temperatura
    # Os extremos devem usar somente medições completas e válidas, como os cards.
    for measurement in valid_measurements(
        collection, {"$gte": start, "$lt": end, "$lte": observed_at}
    ):
        minimum = min(minimum, measurement.temperatura)
        maximum = max(maximum, measurement.temperatura)
    return StationReading(
        observedAt=observed_at,
        temperature=latest.temperatura,
        humidity=latest.umidade,
        pressure=latest.pressao,
        illuminance=latest.luminosidade,
        minimum=minimum,
        maximum=maximum,
    )
