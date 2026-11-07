import type { Resource } from "@/types/meteora";

/**
 * CONEXÃO COM A API DO BACKEND PYTHON.
 * Configure METEORA_STATION_URL em .env.local.
 * A rota src/app/api/meteora/route.ts chama esta função somente no servidor.
 * Ajuste aqui autenticação, timeout e cabeçalhos; adapte os campos em contracts.ts.
 * URLs e token não são enviados ao navegador (não usar prefixo NEXT_PUBLIC_).
 */
export async function readBackend<T>(url: string | undefined, parse: (value: unknown) => T): Promise<Resource<T>> {
  if (!url?.trim()) return { status: "unconfigured", data: null };
  try {
    const endpoint = new URL(url);
    if (!["http:", "https:"].includes(endpoint.protocol)) throw new Error("Protocolo inválido");
    const response = await fetch(endpoint, {
      cache: "no-store",
      signal: AbortSignal.timeout(8_000),
      headers: {
        Accept: "application/json",
        ...(process.env.METEORA_API_TOKEN ? { Authorization: `Bearer ${process.env.METEORA_API_TOKEN}` } : {}),
      },
    });
    if (!response.ok) throw new Error("Backend indisponível");
    // API disponível, mas ainda sem medição ou fonte de previsão.
    if (response.status === 204) return { status: "ready", data: null };
    return { status: "ready", data: parse(await response.json()) };
  } catch {
    // Mantém URLs, tokens e detalhes internos de erros fora da resposta pública.
    return { status: "error", data: null };
  }
}
