import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faDroplet } from "@fortawesome/free-solid-svg-icons";
import type { Forecast, Resource } from "@/types/meteora";
import { dayKey, dayLabel, formatNumber } from "@/lib/format";
import Panel from "@/components/ui/Panel";
import EmptyState from "@/components/ui/EmptyState";
import WeatherIcon from "./WeatherIcon";

export default function DailyForecast({ resource, now, loading }: { resource?: Resource<Forecast>; now: Date | null; loading: boolean }) {
  const today = now ? dayKey(now) : "";
  const days = (resource?.data?.daily ?? []).filter((day) => day.date >= today).slice(0, 7);
  const values = days.flatMap((day) => [day.minimum, day.maximum].filter((value): value is number => value !== null));
  const lower = Math.min(...values) - 2;
  const span = Math.max(1, Math.max(...values) - lower + 2);
  return <Panel labelledBy="daily-title" className="min-h-[390px]">
    <p className="eyebrow">TENDÊNCIA</p>
    <div className="mb-4 flex items-center justify-between gap-3">
      <h2 id="daily-title" className="panel-title">Próximos 7 dias</h2>
      <span className="text-[11px] text-meteora-muted">Mín. / Máx.</span>
    </div>
    {days.length === 0 ? <EmptyState loading={loading} error={resource?.status === "error"} /> : (
      <ul className="divide-y divide-meteora-border/65">
        {days.map((day) => <li key={day.date} className="grid grid-cols-[42px_42px_24px_30px_1fr_30px] items-center gap-2 py-3 text-xs sm:grid-cols-[1fr_46px_30px_34px_2fr_34px] sm:gap-3">
          <time dateTime={day.date} className="font-extrabold text-meteora-text">{dayLabel(day.date, today)}</time>
          <span aria-label={`Probabilidade de chuva: ${day.precipitationProbability === null ? "indisponível" : `${day.precipitationProbability}%`}`} className="flex items-center gap-0.5 text-meteora-muted"><FontAwesomeIcon icon={faDroplet} className="size-2.5 text-meteora-accent" />{formatNumber(day.precipitationProbability)}{day.precipitationProbability !== null && "%"}</span>
          <WeatherIcon condition={day.condition} className="size-4" />
          <span className="text-right text-meteora-muted"><span className="sr-only">Mínima: </span>{formatNumber(day.minimum)}{day.minimum !== null && "°"}</span>
          <span aria-hidden="true" className="relative h-1 overflow-hidden rounded-full bg-meteora-muted/15">
            {day.minimum !== null && day.maximum !== null && <span className="absolute inset-y-0 min-w-1 rounded-full bg-linear-to-r from-meteora-accent to-meteora-gold" style={{ left: `${((day.minimum - lower) / span) * 100}%`, width: `${((day.maximum - day.minimum) / span) * 100}%` }} />}
          </span>
          <span className="text-right font-extrabold"><span className="sr-only">Máxima: </span>{formatNumber(day.maximum)}{day.maximum !== null && "°"}</span>
        </li>)}
      </ul>
    )}
  </Panel>;
}
