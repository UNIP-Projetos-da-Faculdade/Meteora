from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response, status
from pymongo.collection import Collection

from app import services
from app.database import get_collection
from app.models import HealthStatus, MeasurementIn, MeasurementOut, StationReading


router = APIRouter(prefix="/api")
Measurements = Annotated[Collection[dict[str, Any]], Depends(get_collection)]
EMPTY = {204: {"description": "Nenhuma medição disponível"}}


@router.post(
    "/medicoes/", response_model=MeasurementOut,
    status_code=status.HTTP_201_CREATED, tags=["Medições"],
)
def create_measurement(measurement: MeasurementIn, collection: Measurements) -> MeasurementOut:
    return services.create_measurement(collection, measurement)


@router.get("/medicoes/", response_model=list[MeasurementOut], tags=["Medições"])
def list_measurements(
    collection: Measurements,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[MeasurementOut]:
    return services.list_measurements(collection, limit)


@router.get(
    "/medicoes/ultima/", response_model=MeasurementOut,
    responses=EMPTY, tags=["Medições"],
)
def latest_measurement(collection: Measurements) -> MeasurementOut | Response:
    latest = services.latest_measurement(collection)
    if latest is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return latest


@router.get("/station/latest", response_model=StationReading, responses=EMPTY, tags=["Dashboard"])
def latest_station_reading(collection: Measurements) -> StationReading | Response:
    latest = services.latest_measurement(collection)
    if latest is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return services.station_reading(collection, latest)


@router.get(
    "/forecast", status_code=status.HTTP_204_NO_CONTENT, tags=["Dashboard"],
    description="Sem provedor meteorológico configurado neste MVP; retorna 204, sem inventar previsões.",
)
def forecast() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/health/", response_model=HealthStatus, tags=["Saúde"])
def health(request: Request) -> HealthStatus:
    request.app.state.database.command("ping")
    return HealthStatus()
