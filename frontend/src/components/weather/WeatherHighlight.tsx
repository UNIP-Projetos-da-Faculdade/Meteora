import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowDown, faArrowUp, faSun, faTemperatureHalf } from "@fortawesome/free-solid-svg-icons";
import type { Forecast, Resource } from "@/types/meteora";
import { dayKey, formatNumber, time, tomorrowKey } from "@/lib/format";
import Panel from "@/components/ui/Panel";
import EmptyState from "@/components/ui/EmptyState";

export default function WeatherHighlight({ resource, now, loading }: { resource?: Resource<Forecast>; now: Date | null; loading: boolean }) {
  const forecast = resource?.data;
  const today = now ? forecast?.daily.find((day) => day.date === dayKey(now)) : null;
  const tomorrow = now ? forecast?.daily.find((day) => day.date === tomorrowKey(now)) : null;
  const difference = today?.maximum != null && tomorrow?.maximum != null ? tomorrow.maximum - today.maximum : null;
  const sunrise = forecast?.sunrise;
  const sunset = forecast?.sunset;
  const hasSun = Boolean(now && sunrise && sunset && dayKey(sunrise) === dayKey(now) && dayKey(sunset) === dayKey(now));
  const progress = hasSun && now && sunrise && sunset ? Math.max(0, Math.min(1, (now.getTime() - Date.parse(sunrise)) / (Date.parse(sunset) - Date.parse(sunrise)))) : null;
  const sunX = progress === null ? 0 : 24 + progress * 252;
  // Mesma curva quadrática do SVG: o marcador permanece sobre o arco solar.
  const sunY = progress === null ? 0 : 82 - 238 * progress * (1 - progress);

  return <Panel labelledBy="highlight-title" className="min-h-[390px] bg-linear-to-bl from-meteora-accent/15 to-transparent">
    <p className="eyebrow">DESTAQUE</p>
    <div className="flex items-center justify-between gap-3">
      <h2 id="highlight-title" className="panel-title">{difference === null ? "No ritmo do tempo" : difference < 0 ? "Amanhã mais fresco" : difference > 0 ? "Amanhã mais quente" : "Temperatura estável"}</h2>
      <FontAwesomeIcon icon={faTemperatureHalf} className="size-4 text-meteora-accent" />
    </div>
    {difference === null ? <EmptyState compact loading={loading} error={resource?.status === "error"} /> : <div className="mt-6">
      <p className="flex items-center gap-2 text-5xl font-semibold tracking-tight text-meteora-gold">{formatNumber(Math.abs(difference), difference % 1 === 0 ? 0 : 1)}°{difference !== 0 && <FontAwesomeIcon icon={difference < 0 ? faArrowDown : faArrowUp} className="size-6" />}</p>
      <p className="mt-3 text-xs leading-relaxed text-meteora-muted">{difference === 0 ? `A máxima prevista permanece em ${formatNumber(tomorrow?.maximum)}°.` : `A máxima prevista ${difference < 0 ? "cai" : "sobe"} de ${formatNumber(today?.maximum)}° para ${formatNumber(tomorrow?.maximum)}°.`}</p>
    </div>}
    <div className="mt-4">
      <svg aria-hidden="true" viewBox="0 0 300 95" className="mx-auto h-24 w-full max-w-80">
        <path d="M12 82h276" stroke="#A7B8D6" strokeOpacity=".3" />
        <path d="M24 82Q150-37 276 82" fill="none" stroke={hasSun ? "#F6CF86" : "#A7B8D6"} strokeOpacity={hasSun ? 1 : .2} strokeWidth="1.7" strokeDasharray="3 4" />
        {hasSun && progress !== null && progress > 0 && progress < 1 && <circle cx={sunX} cy={sunY} r="6" fill="#F6CF86" />}
      </svg>
      <div className="flex justify-between gap-2 text-[11px] text-meteora-muted">
        <span><FontAwesomeIcon icon={faSun} className="mr-1 size-3 text-meteora-accent" />Nascer · {hasSun && sunrise ? time(sunrise) : "—"}</span>
        <span>Pôr do sol · {hasSun && sunset ? time(sunset) : "—"}</span>
      </div>
    </div>
  </Panel>;
}
