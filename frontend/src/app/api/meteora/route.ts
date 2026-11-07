import { readBackend } from "@/lib/backend";
import { parseStation } from "@/lib/contracts";
import type { DashboardResponse } from "@/types/meteora";
import { connection } from "next/server";

export async function GET() {
  // Executa em cada consulta, inclusive quando ainda não há URLs configuradas.
  await connection();
  const station = await readBackend(process.env.METEORA_STATION_URL, parseStation);
  // Mantém o envelope existente; o painel atual consulta somente a estação.
  return Response.json({ station, forecast: { status: "unconfigured", data: null } } satisfies DashboardResponse, {
    headers: { "Cache-Control": "no-store" },
  });
}
