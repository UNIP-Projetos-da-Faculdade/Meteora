import type { DashboardResponse, DailyForecast, Forecast, HourlyForecast, Resource, StationReading, WeatherCondition } from "../types/meteora";

// O JSON externo é unknown: TypeScript sozinho não valida respostas de uma API.
// Estes adaptadores são o lugar para ajustar nomes/campos ao contrato do backend.

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Objeto inválido");
  }
  return value as Record<string, unknown>;
}

function number(value: unknown, min = -Infinity, max = Infinity): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value !== "number" || !Number.isFinite(value) || value < min || value > max) {
    throw new Error("Medição inválida");
  }
  return value;
}

function timestamp(value: unknown): string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value) || !Number.isFinite(Date.parse(value))) {
    throw new Error("Data inválida: informe ISO 8601 com fuso horário");
  }
  date(value.slice(0, 10));
  return value;
}

function date(value: unknown): string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error("Dia inválido");
  const parsed = new Date(`${value}T12:00:00Z`);
  if (!Number.isFinite(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) throw new Error("Dia inválido");
  return value;
}

function condition(value: unknown): WeatherCondition | null {
  if (value === null || value === undefined) return null;
  if (!["clear", "partly-cloudy", "cloudy", "rain", "storm"].includes(value as string)) throw new Error("Condição inválida");
  return value as WeatherCondition;
}

function checkRange(minimum: number | null, maximum: number | null) {
  if (minimum !== null && maximum !== null && minimum > maximum) throw new Error("Mínima maior que máxima");
}

export function parseStation(value: unknown): StationReading {
  const data = object(value);
  const minimum = number(data.minimum);
  const maximum = number(data.maximum);
  checkRange(minimum, maximum);
  return {
    observedAt: timestamp(data.observedAt),
    temperature: number(data.temperature),
    humidity: number(data.humidity, 0, 100),
    pressure: number(data.pressure, 0),
    illuminance: number(data.illuminance, 0),
    rain24h: number(data.rain24h, 0),
    lightRelative: number(data.lightRelative, 0, 100),
    airRaw: number(data.airRaw, 0),
    minimum,
    maximum,
    feelsLike: number(data.feelsLike),
  };
}

export function parseForecast(value: unknown): Forecast {
  const data = object(value);
  if (!Array.isArray(data.hourly) || !Array.isArray(data.daily)) throw new Error("Previsões inválidas");
  const hourly: HourlyForecast[] = data.hourly.map((value) => {
    const item = object(value);
    return {
      at: timestamp(item.at),
      temperature: number(item.temperature),
      precipitationProbability: number(item.precipitationProbability, 0, 100),
      condition: condition(item.condition),
    };
  });
  const daily: DailyForecast[] = data.daily.map((value) => {
    const item = object(value);
    const minimum = number(item.minimum);
    const maximum = number(item.maximum);
    checkRange(minimum, maximum);
    return {
      date: date(item.date), minimum, maximum,
      precipitationProbability: number(item.precipitationProbability, 0, 100),
      condition: condition(item.condition),
    };
  });
  if (new Set(hourly.map((item) => Date.parse(item.at))).size !== hourly.length || new Set(daily.map((item) => item.date)).size !== daily.length) {
    throw new Error("Previsões duplicadas");
  }
  const sunrise = data.sunrise == null ? null : timestamp(data.sunrise);
  const sunset = data.sunset == null ? null : timestamp(data.sunset);
  if (sunrise && sunset && Date.parse(sunrise) >= Date.parse(sunset)) throw new Error("Horários solares inválidos");
  return {
    updatedAt: timestamp(data.updatedAt),
    hourly: hourly.sort((a, b) => Date.parse(a.at) - Date.parse(b.at)),
    daily: daily.sort((a, b) => a.date.localeCompare(b.date)),
    sunrise, sunset,
  };
}

export function parseDashboard(value: unknown): DashboardResponse {
  const data = object(value);
  function resource<T>(value: unknown, parse: (value: unknown) => T): Resource<T> {
    const item = object(value);
    if (item.status === "ready") return { status: "ready", data: item.data === null ? null : parse(item.data) };
    if (item.status === "error" || item.status === "unconfigured") return { status: item.status, data: null };
    throw new Error("Estado de integração inválido");
  }
  return { station: resource(data.station, parseStation), forecast: resource(data.forecast, parseForecast) };
}
