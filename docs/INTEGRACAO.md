# Integração e dados

## Origem e significado dos campos

Uma medição reúne as leituras do DHT22, BMP280 e BH1750 realizadas no ciclo
do ESP32. O firmware envia os quatro valores em JSON, sem incluir unidades
nos campos numéricos.

| Campo enviado pelo ESP32 | Origem | Unidade | Campo entregue ao painel |
| --- | --- | --- | --- |
| `temperatura` | DHT22 | °C | `temperature` |
| `umidade` | DHT22 | % | `humidity` |
| `pressao` | BMP280 | hPa | `pressure` |
| `luminosidade` | BH1750 | lux | `illuminance` |

O backend preserva as grandezas e unidades recebidas. O firmware já faz a
conversão de pressão de Pa para hPa. A luminosidade permanece em lux.

## Entrada do ESP32

| Propriedade | Contrato |
| --- | --- |
| Método | `POST` |
| Rota | `/api/medicoes/` |
| Cabeçalho | `Content-Type: application/json` |
| Campos obrigatórios | `temperatura`, `umidade`, `pressao`, `luminosidade` |
| Formato dos valores | Números JSON finitos; o firmware utiliza duas casas decimais |
| Autenticação | Não exigida na ingestão do MVP |
| Sucesso | HTTP 201 com a medição registrada e seu identificador |

A API não exige campos adicionais ao firmware. Os quatro números são
preservados mesmo quando estão fora das faixas físicas, incluindo os códigos
de falha do BH1750, como `-1` e `-2`. Isso permite gravar os demais sensores
do mesmo ciclo. Strings, valores nulos, NaN, infinito e campos adicionais
são rejeitados com HTTP 422.

## Persistência e horário

O servidor acrescenta `timestamp` no momento do registro, em UTC. O campo é
gravado como data BSON na coleção `medicoes`. O MongoDB acrescenta `_id`.
Nas respostas da API, esse identificador é convertido para a string `id`,
e o horário é serializado em ISO 8601 com fuso.

O firmware não envia o horário da aquisição. Por isso, o timestamp representa
o registro no servidor. O frontend usa o fuso `America/Sao_Paulo` para apresentar
os horários ao usuário.

O histórico é retornado do registro mais recente para o mais antigo. Documentos
sem timestamp BSON ou com medições incompatíveis permanecem no banco, mas
não entram nas respostas nem no cálculo dos extremos.

## Consultas disponíveis

| Método | Endpoint | Finalidade |
| --- | --- | --- |
| `GET` | `/api/medicoes/` | Consultar o histórico recente das medições válidas |
| `GET` | `/api/medicoes/ultima/` | Consultar a última medição válida no formato de armazenamento |
| `GET` | `/api/station/latest` | Obter a última leitura adaptada ao painel, com mínima e máxima |
| `GET` | `/api/health/` | Verificar a comunicação da API com o MongoDB |

O histórico aceita `limit`, com padrão 100 e valores de 1 a 1000. Sem medições
válidas, ele retorna um array vazio. As rotas de última leitura retornam
HTTP 204, sem corpo, quando ainda não há dados válidos.

O endpoint `/api/forecast` permanece por compatibilidade e retorna HTTP 204.
Ele não é consultado pelo painel atual, que utiliza os dados da estação.

## Contrato consumido pelo frontend

`GET /api/station/latest` retorna `observedAt`, as quatro grandezas em inglês
e os campos `minimum` e `maximum`. O horário vem de `timestamp`. Os extremos
usam temperaturas observadas no dia da última medição, no horário de Brasília.

O Next.js recebe esse objeto, valida seu formato e o publica em `/api/meteora`
dentro do recurso `station`, com `status` e `data`:

| Estado | Significado |
| --- | --- |
| `ready`, com `data` | A resposta contém uma leitura válida |
| `ready`, com `data` nulo | A API respondeu 204 e ainda não há leitura disponível |
| `unconfigured` | A URL da estação não foi configurada |
| `error` | Houve falha HTTP, timeout ou resposta incompatível |

Umidade fora de 0 a 100, pressão negativa e luminosidade negativa são
convertidas para `null` somente na resposta do Next.js. O card correspondente
mostra `—` e “Leitura indisponível”; os demais valores continuam atualizando.
O backend, o histórico da API e o MongoDB preservam o número original.
Temperaturas negativas e valores iguais a zero continuam sendo apresentados.

O envelope mantém `forecast` com estado `unconfigured` por compatibilidade.
Os campos opcionais de chuva, leitura de ar, luz relativa e sensação térmica
também podem permanecer nulos no contrato da API e não são mostrados pelo painel.

O servidor Next.js usa timeout de 8 segundos para consultar o backend. O
navegador atualiza o painel a cada 30 segundos enquanto a aba está visível,
ao retornar para ela ou pelo botão de atualização. Uma consulta com erro
preserva a última leitura disponível na interface e apresenta o aviso de falha.

## Configuração dos endereços

| Configuração | Onde é definida | Para que serve |
| --- | --- | --- |
| `ssid` e `password` | Firmware | Conectar o ESP32 à rede Wi-Fi |
| `servidor` | Firmware | Informar o endereço HTTP do backend, terminado em `/api/medicoes/` |
| `MONGODB_URI` | Ambiente do backend ou `backend/.env` | Conectar o FastAPI ao MongoDB |
| `MONGODB_DATABASE` | Ambiente do backend ou `backend/.env` | Selecionar o banco de dados |
| `CORS_ORIGINS` | Ambiente do backend ou `backend/.env` | Definir origens permitidas para acessos de navegador à API |
| `METEORA_STATION_URL` | Ambiente do Next.js ou `frontend/.env.local` | Consultar `/api/station/latest` no backend |

O ESP32 utiliza o IP de rede do computador que executa o backend. Quando
Next.js e FastAPI estão no mesmo computador, a URL usada pelo Next.js pode
ser local. A conexão com o MongoDB é responsabilidade do backend.

Procedimentos de execução e verificação da rede:
[README da raiz](../README.md) e [Começar aqui](../COMECAR-AQUI.md).
