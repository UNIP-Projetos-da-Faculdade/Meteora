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

1. Defina as URLs completas em `METEORA_STATION_URL` e `METEORA_FORECAST_URL`, no `.env.local`.
2. Confira o contrato proposto em [BACKEND.md](./BACKEND.md).
3. Se o JSON Python tiver outros nomes, adapte-o em `src/lib/contracts.ts`.
4. Reinicie o Next.js após alterar variáveis de ambiente.

```text
ESP32 → backend Python ─────┐
Fonte de previsão → backend ┤
                           ↓
src/lib/backend.ts → /api/meteora → useDashboard → componentes
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
│   ├── weather/                # Atual, previsão horária, diária e destaque
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
Leituras da estação com mais de 90 segundos e previsões com mais de 6 horas são
identificadas como desatualizadas. Falhas preservam a última resposta válida em memória,
identificando-a na tela. Não há persistência local de medições.

O seletor Hoje/Amanhã usa o horário de Brasília. Curvas e barras são SVG/CSS,
calculadas com os dados recebidos. Campos ausentes aparecem como `—`; zero é válido.
O sensor de ar exibe ADC bruto, sem inferir qualidade do ar. A luminosidade do
BH1750 é recebida em `illuminance` e exibida em lux, sem converter para percentual.
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
