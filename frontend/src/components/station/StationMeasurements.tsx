import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCloudRain, faDroplet, faGauge, faSun, faTemperatureHalf, faWind } from "@fortawesome/free-solid-svg-icons";
import type { Resource, StationReading } from "@/types/meteora";
import { formatNumber, time } from "@/lib/format";
import Panel from "@/components/ui/Panel";

export default function StationMeasurements({ resource, stale, loading }: { resource?: Resource<StationReading>; stale: boolean; loading: boolean }) {
  const data = resource?.data;
  const measurements = [
    { label: "Temperatura", value: data?.temperature, unit: "°C", icon: faTemperatureHalf, detail: "Temperatura do ar", digits: 1 },
    { label: "Umidade", value: data?.humidity, unit: "%", icon: faDroplet, detail: "Umidade relativa", digits: 0 },
    { label: "Pressão", value: data?.pressure, unit: " hPa", icon: faGauge, detail: "Pressão atmosférica", digits: 0 },
    { label: "Chuva · 24 h", value: data?.rain24h, unit: " mm", icon: faCloudRain, detail: "Precipitação acumulada", digits: 1 },
    { label: "Luminosidade", value: data?.illuminance, unit: " lux", icon: faSun, detail: "Iluminância · BH1750", digits: 1 },
    { label: "Sensor de ar", value: data?.airRaw, unit: " ADC", icon: faWind, detail: "Leitura bruta · sem índice de qualidade", digits: 0 },
  ];
  return <Panel id="estacao" labelledBy="station-title">
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p className="eyebrow">MEDIÇÕES LOCAIS</p>
        <h2 id="station-title" className="panel-title">Nossa estação</h2>
        <p className="mt-1 text-xs leading-relaxed text-meteora-muted">Telemetria do ESP32 · consulta a cada 30 segundos{data && ` · última leitura às ${time(data.observedAt)}`}</p>
      </div>
      <span className={`rounded-full border border-meteora-border px-3 py-1.5 text-[11px] ${data && !stale ? "text-meteora-mint" : "text-meteora-muted"}`}>
        {loading ? "Conectando…" : resource?.status === "error" ? "Conexão indisponível" : stale ? "Leitura desatualizada" : data ? "Estação conectada" : "Aguardando estação"}
      </span>
    </div>
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {measurements.map((item) => <div key={item.label} className="min-w-0 rounded-2xl border border-meteora-border bg-meteora-bg/65 p-3.5">
        <dt className="flex items-center gap-1.5 text-xs text-meteora-muted"><FontAwesomeIcon icon={item.icon} className="size-3.5 shrink-0 text-meteora-accent" />{item.label}</dt>
        <dd className="mt-2 whitespace-nowrap text-lg font-extrabold tabular-nums">{formatNumber(item.value, item.digits)}{item.value != null && <span>{item.unit}</span>}</dd>
        <dd className="mt-1 text-[10px] leading-relaxed text-meteora-muted">{item.detail}</dd>
      </div>)}
    </dl>
    {!data && <p className="mt-4 text-xs text-meteora-muted">{resource?.status === "error" ? "Não foi possível obter as medições. Tentaremos novamente automaticamente." : "Nenhuma medição recebida. Os valores aparecerão quando a estação enviar uma leitura."}</p>}
  </Panel>;
}
