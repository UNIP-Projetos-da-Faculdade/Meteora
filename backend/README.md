# Backend Meteora

Para executar com atalhos no Windows, testar com dados fictícios e orientar a
pessoa que ficará com o ESP32, comece por [COMECAR-AQUI.md](../COMECAR-AQUI.md).

API REST para a estação ESP32, com Python 3.12+, FastAPI, Uvicorn, PyMongo,
MongoDB, Pydantic e pydantic-settings. A entrada segue o firmware existente:
DHT22 (°C e %), BMP280 (hPa) e BH1750 (lux), enviados a cada 10 segundos.

## Arquitetura

```text
ESP32 → POST /api/medicoes/ → validação Pydantic → MongoDB.medicoes
Next.js → GET /api/station/latest → última medição + extremos do dia
Navegador → /api/meteora do Next.js → dashboard
```

- `app/main.py`: aplicação, ciclo de vida da conexão, CORS e erros públicos.
- `app/config.py`: configuração por ambiente e arquivo `backend/.env`.
- `app/database.py`: coleção e índice composto `timestamp DESC, _id DESC`.
- `app/models.py`: contratos de entrada e saída.
- `app/routers.py`: endpoints REST.
- `app/services.py`: persistência, histórico e mínima/máxima.
- `tests/`: requisições simuladas sem hardware e integração opcional com MongoDB real.

As rotas que usam PyMongo são síncronas e executadas pelo FastAPI em threads.
Uma conexão é compartilhada durante a vida da aplicação e fechada ao encerrar.
O índice é criado no início; se o banco estiver indisponível, a API mantém
`/docs` acessível e tenta criar o índice novamente nas próximas consultas.

## Instalação e configuração

Na raiz do repositório, em PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Para executar apenas a aplicação, instale `requirements.txt`. Os comandos usam
o Python do ambiente virtual diretamente, sem depender da ativação no PowerShell.
Em Linux/macOS, use `python3 -m venv .venv` e `.venv/bin/python`.

| Variável | Padrão | Uso |
| --- | --- | --- |
| `MONGODB_URI` | Obrigatório no ambiente/`.env` | Exemplo local: `mongodb://127.0.0.1:27017`; também aceita Atlas |
| `MONGODB_DATABASE` | Obrigatório no ambiente/`.env` | Use `meteora`; a coleção é `medicoes` |
| `MONGODB_TIMEOUT_MS` | `2000` | Timeout de seleção, conexão e socket, entre 100 e 30000 ms |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Origens permitidas, separadas por vírgula |

Variáveis do processo têm prioridade sobre `.env`. O arquivo `.env` e o ambiente
virtual são ignorados pelo Git. Insira credenciais somente no ambiente local.

## MongoDB

Use uma instalação local do MongoDB Community ou, se já tiver Docker:

```bash
docker run --name meteora-mongodb -d -p 27017:27017 -v meteora-mongodb-data:/data/db mongo:8.0
```

O volume preserva os dados ao reiniciar o contêiner. Para iniciá-lo novamente:

```bash
docker start meteora-mongodb
```

Com MongoDB Community instalado, também é possível iniciar `mongod` manualmente:

```powershell
New-Item -ItemType Directory -Force .cache\mongo-data
mongod --dbpath .cache\mongo-data --bind_ip 127.0.0.1 --port 27017
```

No Atlas, crie um banco/usuário, autorize o endereço de rede do servidor e
configure a URI fornecida pelo painel em `MONGODB_URI`. O usuário precisa poder
ler, gravar, agregar e criar índices no banco configurado. A coleção e o índice
são criados pela aplicação. Não é necessário expor o MongoDB ao ESP32.

## Iniciar a API

Dentro de `backend/`, com o MongoDB em execução:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Se o ambiente virtual estiver ativado, o comando equivalente é:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger: <http://127.0.0.1:8000/docs>. Esquema: <http://127.0.0.1:8000/openapi.json>.
Saúde do banco: <http://127.0.0.1:8000/api/health/>.

## Endpoints

| Método | Rota | Resultado |
| --- | --- | --- |
| POST | `/api/medicoes/` | Grava uma medição; HTTP 201 |
| GET | `/api/medicoes/?limit=100` | Array do histórico, mais recente primeiro; HTTP 200 |
| GET | `/api/medicoes/ultima/` | Última medição; HTTP 200 ou 204 sem dados |
| GET | `/api/station/latest` | Objeto para o dashboard; HTTP 200 ou 204 sem dados |
| GET | `/api/forecast` | HTTP 204: ainda sem provedor meteorológico |
| GET | `/api/health/` | HTTP 200 com `{"status":"ok","database":"ok"}` ou 503 |

`limit` é inteiro, padrão 100, mínimo 1 e máximo 1000. O histórico vazio retorna
`[]`. Leituras com mesmo timestamp usam `_id` decrescente como desempate.
As consultas usam apenas documentos com timestamp BSON e os quatro campos
válidos. Registros antigos ou inseridos manualmente com campos incompletos
permanecem no MongoDB e são ignorados no histórico, última leitura e extremos.
Se não houver uma medição compatível, o histórico retorna `[]` e as rotas de
última leitura retornam 204; nenhum horário é inventado para registros antigos.
Os timestamps são gerados pelo servidor em UTC, armazenados como data BSON
(precisão de milissegundos) e serializados em ISO 8601 com fuso. `_id` é exposto
como string `id` nas rotas de medições.

Os quatro campos são obrigatórios e aceitam números JSON, incluindo inteiros.
Strings numéricas, booleanos, `null`, NaN, infinito, campos adicionais e timestamps
informados pelo cliente são rejeitados. Umidade deve estar entre 0 e 100;
pressão e luminosidade devem ser não negativas. Temperatura aceita valores
negativos. Zero é uma medição válida e não representa ausência.

Erros de validação retornam HTTP 422 com `detail` contendo `loc`, `msg` e `type`.
Falhas do PyMongo retornam HTTP 503:

```json
{"detail":"MongoDB indisponível. Tente novamente."}
```

As respostas de erro não incluem URI nem credenciais do banco.
Não há autenticação na ingestão do MVP; o firmware atual não envia credenciais.

### Simular o ESP32

Em bash, macOS ou Linux:

```bash
curl -i -X POST http://127.0.0.1:8000/api/medicoes/ \
  -H 'Content-Type: application/json' \
  -d '{"temperatura":27.5,"umidade":65.2,"pressao":1013.25,"luminosidade":350.8}'
```

Em PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/medicoes/ -ContentType 'application/json' -Body '{"temperatura":27.5,"umidade":65.2,"pressao":1013.25,"luminosidade":350.8}'
```

Exemplo ilustrativo da resposta HTTP 201 (id e horário variam):

```json
{
  "id": "690f62000000000000000001",
  "temperatura": 27.5,
  "umidade": 65.2,
  "pressao": 1013.25,
  "luminosidade": 350.8,
  "timestamp": "2026-11-06T20:30:00Z"
}
```

Após essa única medição, `GET /api/station/latest` retorna:

```json
{
  "observedAt": "2026-11-06T20:30:00Z",
  "temperature": 27.5,
  "humidity": 65.2,
  "pressure": 1013.25,
  "illuminance": 350.8,
  "minimum": 27.5,
  "maximum": 27.5,
  "rain24h": null,
  "lightRelative": null,
  "airRaw": null,
  "feelsLike": null
}
```

Mínima e máxima são temperaturas **observadas**, agregadas no dia da última
medição em `America/Sao_Paulo`, até o instante dessa leitura. Não são previsão.
Assim, uma leitura antiga continua acompanhada dos extremos do mesmo dia.
`tzdata` garante esse fuso também em instalações Windows.

## Integração com o ESP32

O arquivo `firmware/sketch_oct31a/sketch_oct31a.ino` foi mantido no estado original.
Ele faz POST para `http://10.0.0.114:8000/api/medicoes/` e espera HTTP 201. O
comentário “API DJANGO” é antigo; o contrato HTTP é compatível com este FastAPI.
Nenhuma placa ou conexão USB é necessária para testar o simulador e o dashboard.

Execute a API no computador acessível pelo ESP32, na mesma rede Wi-Fi. Se o IP
do computador for diferente, a pessoa responsável pelo teste físico precisará
conferir o campo `servidor` e os campos Wi-Fi já existentes no firmware.
Use o IP da máquina, nunca `localhost`
na ESP32. Permita conexões de entrada à porta 8000 na rede local pelo firewall.
O hardware físico continua necessário para validar sensores, Wi-Fi e acesso pela LAN.

### Simulador contínuo e limpeza dos testes

Com a API aberta, na raiz do repositório execute `simular-dados.cmd`, ou, em
`backend/`, `.\.venv\Scripts\python.exe -m scripts.simular_esp32`. O padrão envia
uma medição a cada 10 segundos até Ctrl+C. Para limitar os envios, acrescente
`--count 3 --interval 2`. Cada POST usa os quatro campos reais e deve retornar 201.

Depois de parar o simulador, `limpar-dados-simulados.cmd` remove somente os ids
registrados por ele em `backend/.cache/simulacoes/`, com a mesma configuração de
banco. Não remove medições anteriores nem dados enviados pelo hardware. Não
apague os diários antes de limpar. Os scripts nunca inserem dados fictícios
automaticamente durante o início da API.

## Integração com o frontend e divergências resolvidas

Em `frontend/.env.local`, configure e reinicie o Next.js:

```dotenv
METEORA_STATION_URL=http://127.0.0.1:8000/api/station/latest
METEORA_FORECAST_URL=
METEORA_API_TOKEN=
```

Se Next.js estiver em outra máquina/contêiner, use um endereço do backend
acessível por esse servidor. O navegador continua consultando `/api/meteora`.
O token opcional do frontend não é necessário neste MVP.

O firmware é a fonte de verdade da ingestão. A API oferece uma projeção em inglês
para manter o contrato existente do dashboard. Não foi encontrado documento de
requisitos da disciplina no repositório. `frontend/BACKEND.md` foi preservado;
as diferenças em relação ao contrato proposto estão documentadas aqui:

1. O BH1750 envia lux, mas a tela anterior esperava LDR em %. Foi acrescentado
   `illuminance` aos tipos/parser e o card agora mostra lux. `lightRelative`
   continua aceito pelo parser e retorna `null`; não há conversão arbitrária.
2. Chuva, ADC de ar e sensação térmica não são fornecidos pelo firmware e
   retornam `null`. Mínima e máxima usam somente medições persistidas.
3. O documento previa HTTP 204 sem leituras, mas `readBackend` tentava ler JSON
   vazio. O cliente e o parser agora aceitam `ready` com `data: null`.
4. Os gráficos existentes são de **previsão**, não de histórico dos sensores.
   Não há provedor configurado: `/api/forecast` retorna 204 sem dados fabricados.
   Deixe `METEORA_FORECAST_URL` vazio para exibir o estado não configurado ou
   aponte para esse endpoint para indicar uma fonte disponível sem dados.
   Previsões horárias/diárias e horários solares dependem de integração futura.

O histórico das quatro medições já está disponível em `/api/medicoes/`; a tela
atual não contém gráfico desse histórico. Não foram adicionados filtros nem
novos gráficos. O dashboard mantém a consulta de 30 segundos e sinaliza leituras
com mais de 90 segundos como desatualizadas.

## Testes

Dentro de `backend/`, após instalar `requirements-dev.txt`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes padrão usam TestClient e mongomock, sem ESP32, rede ou MongoDB de
produção. Cobrem POST realista, HTTP 201, validação inclusive NaN/Infinity,
persistência de datetime, serialização de ids, histórico, limites, última leitura,
base vazia, extremos na virada do dia de Brasília, CORS, Swagger, indisponibilidade
e recuperação do banco. Mongomock não substitui a validação contra o MongoDB real.

Para executar também a integração real, inicie uma instância de testes e defina:

```powershell
$env:TEST_MONGODB_URI = 'mongodb://127.0.0.1:27017'
.\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:TEST_MONGODB_URI
```

O teste de integração cria e remove somente um banco `meteora_test_<uuid>`.
Sem essa variável, ele é marcado como ignorado. Com a variável, falha caso o
banco esteja inacessível. Para executar somente esse teste, use `-m mongodb`.

Para verificar as alterações de integração do frontend, dentro de `frontend/`:

```powershell
npm.cmd test
npm.cmd run lint
npx.cmd tsc --noEmit
```

As alterações ficam locais para revisão, sem commit ou push automático.
