import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCloud, faCloudBolt, faCloudMoon, faCloudRain, faCloudSun, faMoon, faSun, faMinus } from "@fortawesome/free-solid-svg-icons";
import type { WeatherCondition } from "@/types/meteora";

const labels: Record<WeatherCondition, string> = {
  clear: "Céu limpo", "partly-cloudy": "Parcialmente nublado", cloudy: "Nublado", rain: "Chuva", storm: "Trovoadas",
};

export default function WeatherIcon({ condition, night = false, className = "size-5" }: {
  condition: WeatherCondition | null;
  night?: boolean;
  className?: string;
}) {
  const icons = { clear: night ? faMoon : faSun, "partly-cloudy": night ? faCloudMoon : faCloudSun, cloudy: faCloud, rain: faCloudRain, storm: faCloudBolt };
  return <FontAwesomeIcon icon={condition ? icons[condition] : faMinus} title={condition ? labels[condition] : "Condição indisponível"} className={`${className} text-meteora-accent`} />;
}
