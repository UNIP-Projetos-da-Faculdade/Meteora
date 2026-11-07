# Meteora

Estação meteorológica acadêmica com ESP32, backend FastAPI, MongoDB e painel
Next.js. O painel apresenta **temperatura, umidade, pressão atmosférica e
luminosidade**, além da mínima e máxima observadas no dia da última leitura.

## Documentação do projeto

Para entender o que acontece desde a leitura dos sensores até a exibição no
site, comece por [Funcionamento do projeto](docs/FUNCIONAMENTO.md).
Consulte também a [Arquitetura](docs/ARQUITETURA.md), a documentação de
[Integração e dados](docs/INTEGRACAO.md) e o [índice de documentação](docs/README.md).

**Antes de testar a placa:** o firmware atual está com `ssid` e `password` vazios
e aponta para `http://10.0.0.114:8000/api/medicoes/`. A equipe precisa preencher
o Wi-Fi e conferir o IP do computador que executará o backend. O `.ino` original
foi preservado. O USB serve para gravar o programa e ver o Monitor Serial;
**as medições são enviadas pelo Wi-Fi, por HTTP**.

## Estrutura

```text
Meteora/
├── README.md                 # Visão geral e sequência de execução
├── COMECAR-AQUI.md           # Guia detalhado para quem vai testar
├── docs/                    # Funcionamento, arquitetura e integração dos dados
├── scripts/                 # Atalhos Windows: preparar, iniciar e validar
├── firmware/sketch_oct31a/   # Programa Arduino do ESP32
├── backend/                 # API, configuração, simulador e testes Python
└── frontend/                # Painel web
```

Os atalhos ficam em `scripts/`, pois incluem tanto inicialização quanto testes.
Eles localizam o projeto pela própria pasta: podem ser abertos com dois cliques
ou chamados de qualquer diretório. Os comandos abaixo partem da raiz do projeto.

## Instalar e iniciar no Windows

Instale Python 3.12 ou superior (com **Add python.exe to PATH**), Node.js 22.18
ou superior e MongoDB Community como serviço do Windows. MongoDB Compass é
opcional para visualizar os documentos. Arduino IDE e bibliotecas dos sensores
são necessários somente para compilar/gravar o firmware.

Uma vez em cada computador, com internet:

```powershell
.\scripts\preparar.cmd
```

Esse comando instala as dependências e cria os arquivos locais de configuração,
preservando os que já existirem. Não copie `.venv` e `node_modules` de outro PC.

| Arquivo | Configuração para backend e frontend no mesmo computador |
| --- | --- |
| `backend/.env` | `MONGODB_URI=mongodb://127.0.0.1:27017` e `MONGODB_DATABASE=meteora` |
| `frontend/.env.local` | `METEORA_STATION_URL=http://127.0.0.1:8000/api/station/latest` |

URI e nome do banco vêm do ambiente/`.env`; não há valores padrão para esses
dois campos no código da aplicação. A coleção é `medicoes`. Os arquivos `.env`
locais são ignorados pelo Git; `.env.example` documenta o que configurar.
Reinicie o servidor correspondente depois de alterar sua configuração.

Abra cada comando em uma janela e mantenha as duas abertas:

```powershell
.\scripts\iniciar-backend.cmd
```

```powershell
.\scripts\iniciar-frontend.cmd
```

- Painel: <http://localhost:3000>
- Estado da API e do banco: <http://localhost:8000/api/health/>
- Documentação interativa: <http://localhost:8000/docs>
- Última medição: <http://localhost:8000/api/medicoes/ultima/>

O backend verifica a conexão antes de iniciar. O banco/coleção e o índice são
criados automaticamente. Para encerrar os servidores, pressione Ctrl+C nas
respectivas janelas. O MongoDB pode continuar como serviço do Windows.

## Testar com dados fictícios

Com backend e frontend abertos, execute em uma terceira janela:

```powershell
.\scripts\simular-dados.cmd
```

Uma medição fictícia é enviada a cada 10 segundos. **HTTP 201** confirma a
gravação. No painel, clique em **Atualizar dados** ou espere até 30 segundos.
Para limitar a três envios: `.\scripts\simular-dados.cmd --count 3 --interval 2`.

No Compass, conecte em `mongodb://127.0.0.1:27017`, abra **meteora → medicoes**
e clique em Refresh. Ordene por `{ "timestamp": -1 }` para ver a mais recente.

Pare o simulador com Ctrl+C antes de testar sensores reais. Para remover somente
os ids registrados por ele, mantendo os outros documentos:

```powershell
.\scripts\limpar-dados-simulados.cmd
```

Os ids ficam em `backend/.cache/simulacoes/`. Preserve essa pasta até a limpeza
e use a mesma configuração de banco. Dados inseridos manualmente não fazem
parte dessa limpeza. Registros antigos incompletos são preservados no MongoDB
e ignorados nas consultas da API.

## Contrato exato do ESP32

O firmware usa `POST /api/medicoes/` com `Content-Type: application/json`, sem
autenticação. Ele monta números com duas casas decimais, por exemplo:

```json
{"temperatura":27.50,"umidade":65.20,"pressao":1013.25,"luminosidade":350.80}
```

| Sensor | Campo enviado | Unidade e validação | Campo recebido pelo painel |
| --- | --- | --- | --- |
| DHT22 | `temperatura` | °C, número finito | `temperature` |
| DHT22 | `umidade` | %, entre 0 e 100 | `humidity` |
| BMP280 | `pressao` | hPa, não negativa; o firmware divide Pa por 100 | `pressure` |
| BH1750 | `luminosidade` | lux, não negativa | `illuminance` |

Os quatro campos são obrigatórios. Não envie strings com unidades, campos
extras, `null`, NaN ou infinito. O backend gera `timestamp` em UTC, grava uma
data BSON no MongoDB e retorna **HTTP 201** com o id e a medição. Ele só confirma
sucesso após a inserção no banco. Zero é um valor válido.

```text
ESP32 ──Wi-Fi/POST──> FastAPI :8000 ──> MongoDB / meteora / medicoes
                           ↑
Navegador ──> Next.js :3000 /api/meteora ──GET /api/station/latest──┘
```

O Next.js valida a resposta e atualiza os quatro cards. Datas aparecem no fuso
de Brasília. Após 90 segundos sem nova medição, o painel sinaliza a leitura
como desatualizada. Chuva, qualidade do ar e previsões estão fora deste painel.
Os cards arredondam os números para apresentação; as casas decimais recebidas
continuam disponíveis no MongoDB e nas respostas da API.

## Conectar o ESP32 de verdade

1. Primeiro confirme que o simulador funciona e que `/api/health/` retorna
   `{"status":"ok","database":"ok"}`.
2. No computador do backend, use `ipconfig` e identifique o IPv4 da rede em uso.
   O ESP32 deve alcançar esse computador pela mesma rede.
3. Em outro aparelho nessa rede, abra `http://IP_DO_COMPUTADOR:8000/api/health/`.
   Se não responder, confira firewall/rede antes de gravar o firmware. Permita
   o Python na rede privada, porta 8000. A URI do MongoDB continua local.
4. A pessoa responsável pela placa deve preencher `ssid` e `password` e conferir
   `servidor` no arquivo `firmware/sketch_oct31a/sketch_oct31a.ino`, preservando
   `/api/medicoes/` no final. Use o IP do computador, nunca `localhost`, o IP da
   placa ou `0.0.0.0`. Se esse IP mudar, confira a URL antes do próximo envio.
5. Na Arduino IDE, instale **esp32 by Espressif Systems**, **DHT sensor library
   by Adafruit**, **Adafruit Unified Sensor**, **Adafruit BMP280 Library**,
   **Adafruit BusIO** e **BH1750 by Christopher Laws**. Abra o `.ino`, selecione
   o modelo correto e a porta da placa, verifique e envie o programa.
6. Abra o Monitor Serial em **115200 baud**. Confira o Wi-Fi, `BMP280 OK`,
   `BH1750 OK` e as leituras. A cada 10 segundos, procure **Codigo HTTP: 201**
   e **Medicao salva com sucesso!**.
7. Confira os mesmos valores na última medição da API, no Compass e nos cards
   do painel. As mínimas/máximas são calculadas com as medições do dia.

O programa usa DHT22 no pino 4, SDA 21, SCL 22 e BMP280 em 0x76/0x77. A ligação,
alimentação, cabo USB, placa e sensores precisam ser conferidos fisicamente.
O firmware cancela o envio se alguma leitura for NaN. Leituras fora dos limites
do contrato retornam 422; indisponibilidade do MongoDB retorna 503.

## Validação final reproduzível

Com as dependências instaladas e o MongoDB em execução:

```powershell
.\scripts\validar.cmd
```

O comando executa a verificação das dependências, os testes Python com MongoDB
real, os testes do frontend, lint, TypeScript, build e uma integração HTTP
completa. Essa integração:

- Lê a montagem do JSON, rota, método, cabeçalho e código de sucesso do `.ino`.
- Envia o payload com as mesmas casas decimais para uma API temporária.
- Confere HTTP 201, valores, data BSON UTC, índice, histórico e última medição.
- Inicia uma instância do Next.js e confere os quatro valores em `/api/meteora`.
- Verifica a página e a ausência de leituras após limpar o teste, inclusive
  quando sobra um documento antigo sem timestamp.
- Encerra seus servidores e remove apenas o banco temporário `meteora_test_<uuid>`.

As portas temporárias são escolhidas automaticamente; a configuração `.env` e
o banco do projeto são preservados. O relatório local fica em
`backend/.cache/ultima-validacao.json`. O build pode precisar de internet para
as fontes do Google. Para repetir só a integração com o build existente, use
`.\scripts\validar.cmd --somente-integracao`.

Essa validação comprova o contrato e o fluxo de software. **Ela não substitui
o teste físico de sensores, USB, Wi-Fi e firewall.** Com a rede configurada e
leituras válidas, os quatro campos enviados pelo firmware correspondem ao que
a API recebe, armazena e disponibiliza ao frontend.

Na revisão de 07/11/2026 passaram **81 testes do backend**, incluindo MongoDB
real e o payload extraído do `.ino`, **14 testes do frontend**, lint, TypeScript,
build e a integração HTTP completa. O firmware original também compilou para
**ESP32 Dev Module** (`esp32:esp32:esp32`), sem upload e sem alterações no arquivo.
O preparo foi executado com sucesso em uma pasta separada, com espaços no nome,
criando outro ambiente virtual, instalando as dependências e gerando os `.env`.
No teste físico, selecione o modelo que corresponde à placa utilizada.

Guia detalhado e solução de problemas: [COMECAR-AQUI.md](COMECAR-AQUI.md).
Detalhes da API: [backend/README.md](backend/README.md).
Detalhes do painel: [frontend/README.md](frontend/README.md).
