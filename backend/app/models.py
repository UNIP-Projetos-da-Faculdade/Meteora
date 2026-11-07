from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


FiniteNumber = Annotated[float, Field(strict=True, allow_inf_nan=False)]


class MeasurementIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperatura: FiniteNumber = Field(description="Temperatura do DHT22 em °C")
    umidade: FiniteNumber = Field(ge=0, le=100, description="Umidade relativa em %")
    pressao: FiniteNumber = Field(ge=0, description="Pressão do BMP280 em hPa")
    luminosidade: FiniteNumber = Field(ge=0, description="Iluminância do BH1750 em lux")


class MeasurementOut(MeasurementIn):
    id: str
    timestamp: AwareDatetime


class StationReading(BaseModel):
    observedAt: AwareDatetime
    temperature: FiniteNumber
    humidity: FiniteNumber
    pressure: FiniteNumber
    illuminance: FiniteNumber = Field(description="Iluminância medida em lux")
    minimum: FiniteNumber
    maximum: FiniteNumber
    rain24h: FiniteNumber | None = None
    lightRelative: FiniteNumber | None = None
    airRaw: FiniteNumber | None = None
    feelsLike: FiniteNumber | None = None


class HealthStatus(BaseModel):
    status: str = "ok"
    database: str = "ok"
