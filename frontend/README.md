# Meteora

Para iniciar o projeto completo no Windows e testar sem ESP32, siga
[COMECAR-AQUI.md](../COMECAR-AQUI.md) na raiz do repositório.

Site para acompanhar os dados de uma estação com ESP32 em São José do Rio Preto, SP.
Next.js App Router, React, TypeScript, Tailwind v4, Manrope e Font Awesome gratuito.
Tema noturno fixo, logo e favicon locais; layout responsivo baseado no protótipo.

## Executar

Dentro de `frontend/`, com Node.js 22.18 ou superior:

```bash
npm install
cp .env.example .env.local
npm run dev
```

Abra o endereço exibido pelo Next.js. Sem URLs configuradas, o painel apresenta
os estados de espera. Não há dados meteorológicos fictícios na aplicação.

## Onde conectar o backend

**A conexão com a API Python fica em `src/lib/backend.ts`.**

1. Defina a URL completa em `METEORA_STATION_URL`, no `.env.local`.
2. Confira o contrato proposto em [BACKEND.md](./BACKEND.md).
3. Se o JSON Python tiver outros nomes, adapte-o em `src/lib/contracts.ts`.
4. Reinicie o Next.js após alterar variáveis de ambiente.

```text
ESP32 → backend Python → src/lib/backend.ts → /api/meteora → useDashboard → componentes
```

As URLs e o token ficam no servidor Next.js, sem expor credenciais ao navegador
e sem exigir CORS entre o navegador e a API Python.
O servidor que executa o Next.js precisa conseguir acessar o backend.

## Organização

```text
src/
├── app/
│   ├── api/meteora/route.ts     # Rota intermediária consultada pelo navegador
│   ├── page.tsx                # Cabeçalho, painel e rodapé
│   ├── layout.tsx              # Fonte, metadados, idioma e estilos globais
│   └── globals.css             # Tokens e identidade visual
├── components/
│   ├── Dashboard.tsx           # Compõe seções e informa dados antigos/erros
│   ├── ui/                     # Cabeçalho, cartões e estados vazios
│   ├── weather/                # Temperatura atual e componentes de previsão fora do painel
│   └── station/                # Medições locais do ESP32
├── hooks/useDashboard.ts       # Consulta, repetição e cancelamento de requisições
├── lib/
│   ├── backend.ts              # CONEXÃO HTTP COM A API PYTHON
│   ├── contracts.ts            # Validação e adaptação das respostas
│   └── format.ts               # Números e datas no horário de Brasília
└── types/meteora.ts            # Contratos compartilhados, unidades e estados
```

O painel consulta a cada 30 segundos enquanto a aba está visível e ao retornar à aba.
O botão “Atualizar dados” permite uma nova tentativa manual.
Leituras da estação com mais de 90 segundos são identificadas como desatualizadas.
Falhas preservam a última resposta válida em memória,
identificando-a na tela. Não há persistência local de medições.

O painel mostra os quatro valores enviados pelo firmware: temperatura e umidade
(DHT22), pressão (BMP280) e luminosidade (BH1750). Mínima e máxima são calculadas
pelo backend com medições do dia da leitura. Horários usam Brasília; campos
ausentes aparecem como `—` e zero é válido. A luminosidade é recebida em
`illuminance` e exibida em lux, sem converter para percentual.

Chuva, sensor de ar, sensação térmica, previsões e horários solares não aparecem
na tela. Não são enviados pelos sensores atuais. Previsões exigiriam um provedor
meteorológico e horários solares uma fonte ou cálculo por localização/data.
O painel não consulta `METEORA_FORECAST_URL`; o campo `forecast` permanece
`unconfigured` no envelope de `/api/meteora` para manter o contrato existente.
Os parsers e componentes de previsão continuam disponíveis fora do painel.
O backend FastAPI está documentado em [../backend/README.md](../backend/README.md).
O cenário noturno é decorativo e acompanha a identidade visual fixa do projeto.

## Verificação

```bash
npm run lint
npm test
npx tsc --noEmit
npm run build
```

Os testes usam o executor do Node, sem dependências extras. Cobrem validação de
leituras, previsões, falhas HTTP e independência das fontes. O build precisa
baixar as fontes do Google e permitir os processos/portas locais do Turbopack.
