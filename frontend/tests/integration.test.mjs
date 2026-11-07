import { test } from "node:test";
import assert from "node:assert/strict";
import { parseStation, parseForecast, parseDashboard } from "../src/lib/contracts.ts";
import { readBackend } from "../src/lib/backend.ts";
import { dayKey, tomorrowKey } from "../src/lib/format.ts";

// Dados restritos aos testes: não são importados pela aplicação nem pela interface.
const observedAt = "2026-11-04T19:00:00-03:00";
const station = { observedAt, temperature: 0, humidity: 0, rain24h: 0 };
const forecast = () => ({ updatedAt: observedAt, hourly: [], daily: [] });

test("preserva zero e normaliza leituras ausentes para null", () => {
  const value = parseStation(station);
  assert.equal(value.temperature, 0);
  assert.equal(value.humidity, 0);
  assert.equal(value.rain24h, 0);
  assert.equal(value.pressure, null);
  assert.equal(value.feelsLike, null);
  assert.equal(value.illuminance, null);
});

test("preserva a iluminância do BH1750 em lux, inclusive zero", () => {
  assert.equal(parseStation({ ...station, illuminance: 350.8 }).illuminance, 350.8);
  assert.equal(parseStation({ ...station, illuminance: 0 }).illuminance, 0);
  assert.throws(() => parseStation({ ...station, illuminance: -1 }));
});

test("rejeita medições malformadas e datas sem fuso", () => {
  for (const patch of [{ temperature: "31" }, { temperature: NaN }, { humidity: 101 }, { humidity: -1 }, { rain24h: -1 }, { airRaw: -1 }, { observedAt: "2026-11-04T19:00:00" }, { observedAt: "2026-02-30T19:00:00Z" }, { minimum: 30, maximum: 20 }]) {
    assert.throws(() => parseStation({ ...station, ...patch }));
  }
});

test("aceita previsões vazias sem fabricar condições", () => {
  assert.deepEqual(parseForecast(forecast()), { ...forecast(), sunrise: null, sunset: null });
});

test("ordena previsões recebidas fora de ordem e preserva lacunas", () => {
  const result = parseForecast({ ...forecast(), hourly: [{ at: "2026-11-04T20:00:00-03:00", temperature: null }, { at: observedAt, temperature: 30 }], daily: [{ date: "2026-11-05" }, { date: "2026-11-04", minimum: 0, maximum: 20 }] });
  assert.equal(result.hourly[0].temperature, 30);
  assert.equal(result.hourly[1].temperature, null);
  assert.equal(result.daily[0].minimum, 0);
});

test("rejeita probabilidades, condições, datas e extremos inválidos", () => {
  const items = [{ date: "2026-11-04", precipitationProbability: 101 }, { date: "2026-11-04", condition: "inventado" }, { date: "2026-02-30" }, { date: "2026-11-04", minimum: 32, maximum: 20 }];
  for (const item of items) assert.throws(() => parseForecast({ ...forecast(), daily: [item] }));
  assert.throws(() => parseForecast({ ...forecast(), hourly: null }));
});

test("rejeita previsões duplicadas e horários solares invertidos", () => {
  assert.throws(() => parseForecast({ ...forecast(), daily: [{ date: "2026-11-04" }, { date: "2026-11-04" }] }));
  assert.throws(() => parseForecast({ ...forecast(), sunrise: observedAt, sunset: "2026-11-04T05:00:00-03:00" }));
});

test("calcula hoje e amanhã pelo horário de Brasília, inclusive na virada do ano", () => {
  assert.equal(dayKey("2026-11-05T01:00:00Z"), "2026-11-04");
  assert.equal(tomorrowKey(new Date("2027-01-01T01:00:00Z")), "2027-01-01");
});

test("mantém estados das fontes independentes e rejeita envelopes inválidos", () => {
  const result = parseDashboard({ station: { status: "ready", data: station }, forecast: { status: "error", data: null } });
  assert.equal(result.station.data.temperature, 0);
  assert.equal(result.forecast.status, "error");
  assert.throws(() => parseDashboard({ station: { status: "ready", data: null } }));
  assert.equal(parseDashboard({ station: { status: "ready", data: null }, forecast: { status: "unconfigured", data: null } }).station.data, null);
});

test("não chama a rede enquanto o endpoint estiver vazio", async (t) => {
  const fetch = t.mock.method(globalThis, "fetch", () => { throw new Error("Não deveria chamar"); });
  assert.deepEqual(await readBackend("", parseStation), { status: "unconfigured", data: null });
  assert.equal(fetch.mock.callCount(), 0);
});

test("consulta a API sem cache e valida a resposta", async (t) => {
  const fetch = t.mock.method(globalThis, "fetch", async () => Response.json(station));
  const result = await readBackend("http://localhost:8000/station", parseStation);
  assert.equal(result.status, "ready");
  assert.equal(result.data.temperature, 0);
  assert.equal(fetch.mock.calls[0].arguments[1].cache, "no-store");
});

test("HTTP inválido, JSON incorreto e timeout viram erros controlados", async (t) => {
  const fetch = t.mock.method(globalThis, "fetch");
  for (const implementation of [async () => new Response("falha interna", { status: 500 }), async () => Response.json({ temperature: "quente" }), async () => { throw new DOMException("Timeout", "TimeoutError"); }]) {
    fetch.mock.mockImplementation(implementation);
    assert.deepEqual(await readBackend("http://localhost:8000/station", parseStation), { status: "error", data: null });
  }
});

test("HTTP 204 indica uma fonte disponível ainda sem dados", async (t) => {
  t.mock.method(globalThis, "fetch", async () => new Response(null, { status: 204 }));
  const result = await readBackend("http://localhost:8000/station", parseStation);
  assert.deepEqual(result, { status: "ready", data: null });
  assert.equal(parseDashboard({ station: result, forecast: { status: "unconfigured", data: null } }).station.data, null);
});

test("uma falha na previsão não descarta a leitura da estação", async (t) => {
  t.mock.method(globalThis, "fetch", async (url) => url.pathname === "/station" ? Response.json(station) : new Response(null, { status: 503 }));
  const [reading, prediction] = await Promise.all([readBackend("http://localhost:8000/station", parseStation), readBackend("http://localhost:8000/forecast", parseForecast)]);
  assert.equal(reading.status, "ready");
  assert.equal(prediction.status, "error");
});
