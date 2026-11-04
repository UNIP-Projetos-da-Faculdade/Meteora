// CONTRATO DE DADOS DO FRONTEND
// A conexão HTTP fica em src/lib/backend.ts; a validação/adaptação, em src/lib/contracts.ts.
// null significa "sem leitura". Zero é uma medição válida e deve continuar aparecendo.
export type WeatherCondition =
  | "clear" | "partly-cloudy" | "cloudy" | "rain" | "storm";

export type StationReading = {
  // Instante da medição no ESP32/backend, em ISO 8601 com fuso (Z ou -03:00).
  observedAt: string;
  // °C, %, hPa, mm nas últimas 24 h, % de luz relativa e contagem ADC, respectivamente.
  temperature: number | null;
  humidity: number | null;
  pressure: number | null;
  rain24h: number | null;
  lightRelative: number | null;
  airRaw: number | null;
  // Campos calculados pelo backend, quando disponíveis. Não são inventados na interface.
  minimum: number | null;
  maximum: number | null;
  feelsLike: number | null;
};

export type HourlyForecast = {
  at: string;
  temperature: number | null;
  precipitationProbability: number | null; // Percentual entre 0 e 100, não fração entre 0 e 1.
  condition: WeatherCondition | null;
};

export type DailyForecast = {
  date: string;
  minimum: number | null;
  maximum: number | null;
  precipitationProbability: number | null;
  condition: WeatherCondition | null;
};

export type Forecast = {
  // Fonte meteorológica, separada das medições locais do ESP32.
  updatedAt: string;
  hourly: HourlyForecast[];
  daily: DailyForecast[];
  sunrise: string | null; // ISO 8601; enviar os horários solares do dia corrente.
  sunset: string | null;
};

export type Resource<T> = {
  // unconfigured: URL não definida; error: requisição/JSON inválido; ready: resposta válida.
  // No navegador, data pode manter a última resposta válida durante uma falha temporária.
  status: "ready" | "unconfigured" | "error";
  data: T | null;
};

export type DashboardResponse = {
  station: Resource<StationReading>;
  forecast: Resource<Forecast>;
};
