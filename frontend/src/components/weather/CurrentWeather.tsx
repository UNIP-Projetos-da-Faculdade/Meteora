import {
  faArrowDown,
  faArrowUp,
  faLocationDot,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { formatNumber } from "@/lib/format";

type CurrentWeatherProps = {
  location: string;
  temperature: number | null;
  description?: string;
  maximum?: number | null;
  minimum?: number | null;
};

export default function CurrentWeather({
  location,
  temperature,
  description,
  maximum,
  minimum,
}: CurrentWeatherProps) {
  return (
    <section
      id="agora"
      aria-labelledby="current-weather-title"
      className="relative isolate scroll-mt-6 overflow-hidden rounded-meteora-hero border border-meteora-accent/30 bg-meteora-surface"
    >
      <svg
        aria-hidden="true"
        focusable="false"
        viewBox="0 0 1160 360"
        preserveAspectRatio="xMidYMid slice"
        className="pointer-events-none absolute inset-0 -z-20 size-full"
      >
        <defs>
          <linearGradient id="weather-sky" x2="0" y2="1">
            <stop offset="0%" stopColor="#182A50" />
            <stop offset="100%" stopColor="#526AA5" />
          </linearGradient>

          <linearGradient id="weather-water" x2="0" y2="1">
            <stop offset="0%" stopColor="#3D5B80" />
            <stop offset="100%" stopColor="#13223E" />
          </linearGradient>

          <radialGradient id="weather-moon-glow">
            <stop offset="0%" stopColor="#C7D8FF" stopOpacity=".3" />
            <stop offset="100%" stopColor="#C7D8FF" stopOpacity="0" />
          </radialGradient>
        </defs>

        <path fill="url(#weather-sky)" d="M0 0h1160v360H0z" />

        <circle
          cx="910"
          cy="100"
          r="150"
          fill="url(#weather-moon-glow)"
        />

        <g fill="#D8E5FF" opacity=".55">
          <circle cx="680" cy="46" r="1.4" />
          <circle cx="818" cy="28" r="1.4" />
          <circle cx="762" cy="92" r="1" />
          <circle cx="998" cy="44" r="1" />
          <circle cx="1082" cy="86" r="1.5" />
          <circle cx="1126" cy="36" r="1" />
        </g>

        <path
          d="M899 58a39 39 0 1 0 58 46 44 44 0 0 1-58-46Z"
          fill="#D5DFF5"
        />

        <path
          d="m0 246 116-28 132 11 145 18 144-19 101-30 70 12 80-27 63 20 52 10 73-32 74 14 110-27v192H0Z"
          fill="#203456"
        />

        <path
          d="m0 268 173-29 149 18 145-13 122 11 90-25 87 16 69-22 88 13 91-21 146 17v127H0Z"
          fill="#172A47"
        />

        <path
          d="M0 252c280-14 436-5 612 9s368 19 548-4v103H0Z"
          fill="url(#weather-water)"
        />

        <g
          stroke="#A4C6FF"
          strokeWidth="1"
          strokeLinecap="round"
          opacity=".18"
        >
          <path d="M792 277h228" />
          <path d="M864 286h71" />
          <path d="M751 296h273" />
          <path d="M821 307h122" />
          <path d="M742 320h289" />
          <path d="M860 331h94" />
          <path d="M800 343h228" />
        </g>

        <path
          d="M0 337c179-30 327-29 473 3l95 20H0Z"
          fill="#0C1730"
        />
      </svg>

      <div className="pointer-events-none absolute inset-0 -z-10 bg-linear-to-r from-meteora-bg/90 via-meteora-bg/45 to-transparent" />

      <div className="flex min-h-[360px] flex-col justify-between gap-8 p-6 sm:p-10">
        <div>
          <p className="text-[10px] font-extrabold tracking-[0.2em] text-meteora-accent">
            ESTAÇÃO ESP32
          </p>

          <h1
            id="current-weather-title"
            className="mt-2 flex items-center gap-2 text-xl font-extrabold tracking-tight text-meteora-text sm:text-2xl"
          >
            <FontAwesomeIcon
              icon={faLocationDot}
              aria-hidden="true"
              className="size-4 shrink-0 text-meteora-accent"
            />

            {location}
          </h1>
        </div>

        <div>
          <p
            aria-label={temperature === null ? "Temperatura indisponível" : `${formatNumber(temperature, 1)} graus Celsius`}
            className="text-[88px] leading-none font-semibold tracking-[-0.07em] text-meteora-text sm:text-[104px]"
          >
            {formatNumber(temperature, temperature !== null && temperature % 1 !== 0 ? 1 : 0)}{temperature !== null && "°"}
          </p>

          <p className="mt-2 text-xl font-extrabold text-meteora-text sm:text-2xl">
            {description ?? (temperature === null ? "Aguardando leitura da estação" : "Temperatura local")}
          </p>

          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-meteora-muted">
            {maximum != null && <span className="inline-flex items-center gap-1">
              <FontAwesomeIcon
                icon={faArrowUp}
                aria-hidden="true"
                className="size-3 text-meteora-accent"
              />
              <span className="sr-only">Máxima:</span>
              {formatNumber(maximum)}°
            </span>}

            {minimum != null && <span className="inline-flex items-center gap-1">
              <FontAwesomeIcon
                icon={faArrowDown}
                aria-hidden="true"
                className="size-3 text-meteora-accent"
              />
              <span className="sr-only">Mínima:</span>
              {formatNumber(minimum)}°
            </span>}

          </div>
        </div>
      </div>
      <p className="absolute right-6 bottom-4 text-[9px] tracking-[0.12em] text-meteora-accent/80 sm:right-8">MEDIÇÕES DA ESTAÇÃO</p>
    </section>
  );
}
