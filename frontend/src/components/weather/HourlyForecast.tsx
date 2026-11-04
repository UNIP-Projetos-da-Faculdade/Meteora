"use client";

import { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faDroplet } from "@fortawesome/free-solid-svg-icons";
import type { Forecast, Resource } from "@/types/meteora";
import { dayKey, formatNumber, time, tomorrowKey } from "@/lib/format";
import Panel from "@/components/ui/Panel";
import EmptyState from "@/components/ui/EmptyState";
import WeatherIcon from "./WeatherIcon";

export default function HourlyForecast({ resource, now, loading }: { resource?: Resource<Forecast>; now: Date | null; loading: boolean }) {
  const [selected, setSelected] = useState<"today" | "tomorrow">("today");
  const selectedDate = now ? selected === "today" ? dayKey(now) : tomorrowKey(now) : "";
  const items = (resource?.data?.hourly ?? []).filter((item) => dayKey(item.at) === selectedDate && (selected === "tomorrow" || !now || Date.parse(item.at) >= now.getTime() - 3_600_000)).slice(0, 8);
  const temperatures = items.flatMap((item) => item.temperature === null ? [] : [item.temperature]);
  const minimum = Math.min(...temperatures);
  const spread = Math.max(1, Math.max(...temperatures) - minimum);
  const x = (index: number) => ((index + .5) / items.length) * 1000;
  const y = (value: number) => 49 - ((value - minimum) / spread) * 30;
  const segments: string[][] = [[]];
  // Uma leitura ausente quebra a curva, em vez de desenhar uma temperatura fictícia.
  items.forEach((item, index) => {
    if (item.temperature === null) segments.push([]);
    else segments[segments.length - 1].push(`${x(index)},${y(item.temperature)}`);
  });

  return (
    <Panel id="previsao" labelledBy="hourly-title">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="eyebrow">PRÓXIMAS HORAS</p>
          <h2 id="hourly-title" className="panel-title">Previsão por hora</h2>
          <p className="mt-1 text-xs text-meteora-muted">Previsão meteorológica para São José do Rio Preto.</p>
        </div>
        <div role="group" aria-label="Dia da previsão" className="flex rounded-xl border border-meteora-border bg-meteora-bg/65 p-1 text-xs">
          {([['today', 'Hoje'], ['tomorrow', 'Amanhã']] as const).map(([value, label]) => (
            <button key={value} type="button" aria-pressed={selected === value} onClick={() => setSelected(value)} className={`rounded-lg px-3 py-2 transition-colors ${selected === value ? "bg-meteora-accent/20 text-meteora-text" : "text-meteora-muted hover:text-meteora-text"}`}>{label}</button>
          ))}
        </div>
      </div>

      {items.length === 0 ? (
        resource?.status === "ready" ? <p className="flex min-h-48 items-center justify-center text-center text-sm text-meteora-muted">Sem previsão disponível para {selected === "today" ? "o restante de hoje" : "amanhã"}.</p> : <EmptyState loading={loading} error={resource?.status === "error"} />
      ) : (
        <div className="mt-6 overflow-x-auto pb-1" tabIndex={0} aria-label="Previsão horária; role horizontalmente em telas pequenas">
          <div className="min-w-[580px]">
            <ul className="grid" style={{ gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))` }}>
              {items.map((item) => {
                const hour = Number(time(item.at).split(":")[0]);
                return <li key={item.at} className="flex flex-col items-center gap-2 text-center">
                  <time dateTime={item.at} className="text-xs text-meteora-muted">{time(item.at)}</time>
                  <WeatherIcon condition={item.condition} night={hour < 6 || hour >= 18} className="my-1 size-6" />
                  <span className="text-lg font-extrabold">{formatNumber(item.temperature)}{item.temperature !== null && "°"}</span>
                  <span className="flex items-center gap-1 text-[11px] text-meteora-muted"><FontAwesomeIcon icon={faDroplet} className="size-2.5 text-meteora-accent" />{formatNumber(item.precipitationProbability)}{item.precipitationProbability !== null && "%"}</span>
                </li>;
              })}
            </ul>
            <svg aria-hidden="true" viewBox="0 0 1000 65" preserveAspectRatio="none" className="mt-2 h-16 w-full overflow-visible">
              <defs><linearGradient id="hourly-line"><stop stopColor="#F6CF86" /><stop offset="100%" stopColor="#A4C6FF" /></linearGradient></defs>
              {segments.filter((segment) => segment.length > 1).map((segment, index) => <polyline key={index} points={segment.join(" ")} fill="none" stroke="url(#hourly-line)" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />)}
              {items.map((item, index) => item.temperature !== null && <circle key={item.at} cx={x(index)} cy={y(item.temperature)} r="3.5" fill="#F4F7FF" />)}
            </svg>
          </div>
        </div>
      )}
      {resource?.data && <p className="mt-2 text-[10px] text-meteora-muted/75">Previsão atualizada às {time(resource.data.updatedAt)}</p>}
    </Panel>
  );
}
