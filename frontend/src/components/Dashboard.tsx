"use client";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowRotateRight, faCircleExclamation } from "@fortawesome/free-solid-svg-icons";
import useDashboard from "@/hooks/useDashboard";
import CurrentWeather from "@/components/weather/CurrentWeather";
import HourlyForecast from "@/components/weather/HourlyForecast";
import DailyForecast from "@/components/weather/DailyForecast";
import WeatherHighlight from "@/components/weather/WeatherHighlight";
import StationMeasurements from "@/components/station/StationMeasurements";
import { time } from "@/lib/format";

export default function Dashboard() {
  const { response, loading, now, retry } = useDashboard();
  const station = response?.station;
  const forecast = response?.forecast;
  const reading = station?.data;
  // Consulta a cada 30 s; após 90 s sem nova medição, a estação fica desatualizada.
  const stale = Boolean(reading && now && (now.getTime() - Date.parse(reading.observedAt) > 90_000 || station?.status === "error"));
  const forecastStale = Boolean(forecast?.data && now && (now.getTime() - Date.parse(forecast.data.updatedAt) > 6 * 3_600_000 || forecast.status === "error"));
  const hasError = station?.status === "error" || forecast?.status === "error";
  const description = reading?.temperature != null
    ? stale ? "Última leitura disponível" : "Temperatura local"
    : loading ? "Buscando leitura da estação…" : station?.status === "error" ? "Leitura da estação indisponível" : "Aguardando leitura da estação";

  return <div className="flex flex-col gap-5">
    <CurrentWeather location="São José do Rio Preto, SP" temperature={reading?.temperature ?? null} description={description} maximum={reading?.maximum} minimum={reading?.minimum} feelsLike={reading?.feelsLike} />

    <div className="flex flex-wrap items-center justify-between gap-3 px-1 text-[11px] text-meteora-muted">
      <p aria-live="polite" className="flex items-center gap-2">
        <span aria-hidden="true" className={`size-1.5 shrink-0 rounded-full ${reading && !stale ? "bg-meteora-mint" : "bg-meteora-muted/50"}`} />
        {loading ? "Consultando a estação…" : reading ? `${stale ? "Última leitura" : "Leitura da estação"} · ${time(reading.observedAt)}` : "Estação aguardando conexão"}
      </p>
      <button type="button" disabled={loading} onClick={retry} className="inline-flex min-h-9 items-center gap-2 rounded-lg px-2 text-meteora-accent transition-colors hover:bg-meteora-surface disabled:cursor-wait disabled:opacity-50">
        <FontAwesomeIcon icon={faArrowRotateRight} className={`size-3 ${loading ? "motion-safe:animate-spin" : ""}`} />{loading ? "Atualizando…" : "Atualizar dados"}
      </button>
    </div>

    {(hasError || stale || forecastStale) && <div role="status" className="flex gap-3 rounded-2xl border border-meteora-gold/20 bg-meteora-gold/5 px-4 py-3 text-xs leading-relaxed text-meteora-muted">
      <FontAwesomeIcon icon={faCircleExclamation} className="mt-0.5 size-4 shrink-0 text-meteora-gold" />
      <p>{hasError ? "Uma das fontes está indisponível. As últimas informações recebidas foram mantidas, quando disponíveis. Tentaremos novamente em até 30 segundos." : `${stale && forecastStale ? "A leitura da estação e a previsão estão desatualizadas" : stale ? "A leitura da estação está desatualizada" : "A previsão está desatualizada"}. Confira os horários de atualização.`}</p>
    </div>}

    <div aria-busy={loading} className="flex flex-col gap-5">
      <HourlyForecast resource={forecast} now={now} loading={loading} />
      <div className="grid gap-5 lg:grid-cols-[1.55fr_1fr]">
        <DailyForecast resource={forecast} now={now} loading={loading} />
        <WeatherHighlight resource={forecast} now={now} loading={loading} />
      </div>
      <StationMeasurements resource={station} stale={stale} loading={loading} />
    </div>
  </div>;
}
