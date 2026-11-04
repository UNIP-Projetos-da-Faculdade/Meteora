import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCloud, faSatelliteDish, faTriangleExclamation } from "@fortawesome/free-solid-svg-icons";

export default function EmptyState({ kind = "forecast", loading = false, error = false, compact = false }: {
  kind?: "forecast" | "station";
  loading?: boolean;
  error?: boolean;
  compact?: boolean;
}) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 text-center ${compact ? "min-h-36" : "min-h-48"}`}>
      <span className="flex size-11 items-center justify-center rounded-full border border-meteora-border bg-meteora-bg/35 text-meteora-accent">
        <FontAwesomeIcon icon={error ? faTriangleExclamation : kind === "station" ? faSatelliteDish : faCloud} className="size-5" />
      </span>
      <p className="text-sm font-semibold text-meteora-text">
        {loading ? "Buscando atualizações…" : error ? "Não foi possível atualizar" : kind === "station" ? "Aguardando leitura da estação" : "Aguardando previsão do tempo"}
      </p>
      <p className="max-w-64 text-xs leading-relaxed text-meteora-muted">
        {error ? "Uma nova tentativa será feita automaticamente." : loading ? "As informações aparecerão aqui assim que estiverem disponíveis." : kind === "station" ? "As medições aparecerão quando a estação estiver conectada." : "A previsão aparecerá quando a fonte de dados estiver disponível."}
      </p>
    </div>
  );
}
