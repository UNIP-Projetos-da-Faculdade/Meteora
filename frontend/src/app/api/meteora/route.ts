import { readBackend } from "@/lib/backend";
import { parseForecast, parseStation } from "@/lib/contracts";
import type { DashboardResponse } from "@/types/meteora";
import { connection } from "next/server";

export async function GET() {
  // Executa em cada consulta, inclusive quando ainda não há URLs configuradas.
  await connection();
  // As fontes são independentes: uma falha na previsão não descarta a telemetria.
  const [station, forecast] = await Promise.all([
    readBackend(process.env.METEORA_STATION_URL, parseStation),
    readBackend(process.env.METEORA_FORECAST_URL, parseForecast),
  ]);
  return Response.json({ station, forecast } satisfies DashboardResponse, {
    headers: { "Cache-Control": "no-store" },
  });
}
