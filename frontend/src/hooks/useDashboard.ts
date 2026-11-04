"use client";

import { useEffect, useState } from "react";
import type { DashboardResponse } from "@/types/meteora";
import { parseDashboard } from "@/lib/contracts";

// O navegador consulta somente a rota interna do Next.js.
// A chamada ao backend Python fica em src/lib/backend.ts, no servidor.
export default function useDashboard() {
  const [response, setResponse] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [now, setNow] = useState<Date | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    let pending = false;
    let controller: AbortController | null = null;

    async function update() {
      if (pending) return;
      pending = true;
      controller = new AbortController();
      const timeout = setTimeout(() => controller?.abort(), 12_000);
      try {
        const result = await fetch("/api/meteora", { cache: "no-store", signal: controller.signal });
        if (!result.ok) throw new Error("Resposta indisponível");
        const next = parseDashboard(await result.json());
        // Uma falha temporária preserva a última leitura. A tela informa que ela está antiga.
        if (active) setResponse((previous) => ({
          station: next.station.status === "error" ? { ...next.station, data: previous?.station.data ?? null } : next.station,
          forecast: next.forecast.status === "error" ? { ...next.forecast, data: previous?.forecast.data ?? null } : next.forecast,
        }));
      } catch {
        if (active) setResponse((previous) => ({
          station: { status: "error", data: previous?.station.data ?? null },
          forecast: { status: "error", data: previous?.forecast.data ?? null },
        }));
      } finally {
        clearTimeout(timeout);
        pending = false;
        if (active) {
          setLoading(false);
          setNow(new Date());
        }
      }
    }

    void update();
    const interval = setInterval(() => {
      setNow(new Date());
      if (document.visibilityState === "visible") void update();
    }, 30_000);
    const onVisible = () => { if (document.visibilityState === "visible") void update(); };
    document.addEventListener("visibilitychange", onVisible);
    // Interrompe a requisição e a atualização periódica ao sair da página.
    return () => {
      active = false;
      controller?.abort();
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [attempt]);

  const retry = () => { setLoading(true); setAttempt((value) => value + 1); };
  return { response, loading, now, retry };
}
