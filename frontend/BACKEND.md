# Integração com a API Python

**Arquivo responsável pela conexão: `src/lib/backend.ts`.**

Este é o contrato proposto pelo frontend, ainda sem um backend real conectado.
`src/types/meteora.ts` documenta os tipos; `src/lib/contracts.ts` valida o JSON
em tempo de execução. Caso a API já tenha outro formato, adapte os parsers nesse arquivo.
Os componentes visuais não precisam conhecer as URLs nem o formato original da API.

## Configuração

Copie `.env.example` para `.env.local`, configure as URLs GET completas e reinicie o Next.js:

```dotenv
# Exemplos de endereços; crie estes endpoints ou informe os seus.
METEORA_STATION_URL=http://127.0.0.1:8000/api/station/latest
METEORA_FORECAST_URL=http://127.0.0.1:8000/api/forecast
METEORA_API_TOKEN=
```

Essas variáveis são privadas do servidor. O token opcional é enviado como
`Authorization: Bearer <token>` aos dois endpoints. Se as fontes usarem credenciais
distintas, ajuste a autenticação em `src/lib/backend.ts`.
O ESP32 envia as leituras ao Python; o navegador consulta somente `/api/meteora` no Next.js.
O backend Python e o firmware continuam fora do escopo deste frontend.

## Estação: resposta JSON

Objeto direto, sem envelope `data`. Exemplo de formato, não de medição real:

```json
{
  "observedAt": "2026-11-04T19:00:00-03:00",
  "temperature": 31.2,
  "humidity": 64,
  "pressure": 1013,
  "rain24h": 2.4,
  "lightRelative": 78,
  "airRaw": 1420,
  "minimum": 24,
  "maximum": 34,
  "feelsLike": 33
}
```

| Campo | Unidade/regra |
| --- | --- |
| `observedAt` | Obrigatório. Instante da medição, ISO 8601 com fuso |
| `temperature`, `minimum`, `maximum`, `feelsLike` | °C; números ou `null` |
| `humidity`, `lightRelative` | Percentual de 0 a 100 |
| `pressure` | hPa, não Pa; valor não negativo |
| `rain24h` | mm acumulados nas últimas 24 horas; não negativo |
| `airRaw` | Contagem ADC bruta; não negativa; não é um índice de qualidade do ar |

Os campos numéricos ausentes ou `null` significam que não há leitura.
Não envie strings com unidades (`"31 °C"`), `NaN`, ou zero como substituto de ausência.
Mínima, máxima e sensação térmica devem vir calculadas do backend se estiverem disponíveis;
o frontend não inventa valores para esses campos.
Se não houver nenhuma leitura válida ainda, retorne HTTP 204; o frontend continuará
sem exibir números e informará indisponibilidade até receber uma leitura válida.

## Previsão: resposta JSON

A previsão deve vir de uma fonte meteorológica. A estação não prevê dias futuros
somente por possuir sensores. O backend pode consultar o provedor e normalizar a resposta:

```json
{
  "updatedAt": "2026-11-04T18:00:00-03:00",
  "hourly": [
    {
      "at": "2026-11-04T19:00:00-03:00",
      "temperature": 30,
      "precipitationProbability": 10,
      "condition": "partly-cloudy"
    }
  ],
  "daily": [
    {
      "date": "2026-11-04",
      "minimum": 24,
      "maximum": 34,
      "precipitationProbability": 10,
      "condition": "partly-cloudy"
    }
  ],
  "sunrise": "2026-11-04T05:39:00-03:00",
  "sunset": "2026-11-04T18:28:00-03:00"
}
```

- `updatedAt`, `hourly` e `daily` são obrigatórios; os arrays podem ser vazios.
- Envie horários suficientes para hoje e amanhã e até sete dias (incluindo hoje).
- `at` usa ISO 8601 com fuso; `date` é o dia local em `YYYY-MM-DD`.
- Temperaturas são °C; probabilidade de precipitação vai de 0 a 100.
- `condition`: `clear`, `partly-cloudy`, `cloudy`, `rain`, `storm` ou `null`.
- `sunrise` e `sunset` são opcionais/nulos e devem pertencer ao dia corrente em Brasília.
- Datas/horas repetidas, probabilidades inválidas e mínima maior que máxima são rejeitadas.
- A interface ordena previsões por data, mostra até oito horários do dia escolhido e até sete dias.
- A curva de temperatura respeita lacunas. O destaque compara a máxima de hoje com a de amanhã.

## Falhas e atualização

Cada fonte tem timeout de 8 segundos e pode falhar independentemente.
A rota interna retorna `{ station: { status, data }, forecast: { status, data } }`,
com `ready`, `unconfigured` (URL vazia) ou `error` (HTTP, timeout ou JSON inválido).
O navegador consulta a cada 30 segundos, cancela a requisição ao sair da página
e preserva a última resposta válida durante falhas temporárias.
Não inclua tokens ou mensagens internas de erro em respostas públicas.
