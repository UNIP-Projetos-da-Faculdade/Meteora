# Funcionamento do projeto

## O que o Meteora faz

O Meteora é uma estação meteorológica que utiliza os dados dos sensores
conectados ao ESP32. A placa lê as condições do ambiente e envia as medições
pela rede Wi-Fi. O backend registra cada medição no MongoDB, e o painel web
consulta o backend para apresentar os valores ao usuário.

O ciclo de operação é:

**Sensores → ESP32 → API FastAPI → MongoDB → API → painel Next.js.**

## 1. Coleta das condições do ambiente

Cada sensor possui uma função no firmware:

| Sensor | O que fornece ao projeto | Unidade |
| --- | --- | --- |
| DHT22 | Temperatura do ar e umidade relativa | °C e % |
| BMP280 | Pressão atmosférica | hPa |
| BH1750 | Luminosidade, expressa como iluminância | lux |

Ao iniciar, o ESP32 configura os sensores e estabelece a conexão Wi-Fi. O
firmware usa o pino 4 para o DHT22 e os pinos 21 e 22 para a comunicação I²C.
O BMP280 é procurado nos endereços 0x76 e 0x77.

A leitura ocorre em ciclos com intervalo de aproximadamente **10 segundos**.
O firmware consulta os sensores e converte a pressão do BMP280 de Pa para hPa,
dividindo o valor por 100.

Se alguma leitura for NaN, indicando ausência de um número válido, o firmware
cancela o envio daquele ciclo. O conjunto enviado precisa conter os quatro
valores; não há envio parcial quando um sensor não fornece uma leitura.

## 2. Envio das medições pelo ESP32

O firmware reúne os valores em um objeto JSON com os campos `temperatura`,
`umidade`, `pressao` e `luminosidade`. Os números são serializados com duas
casas decimais, sem incluir as unidades no texto.

O ESP32 envia esse JSON por uma requisição **HTTP POST** para
`/api/medicoes/`, no computador que executa o backend. O cabeçalho
`Content-Type: application/json` informa o formato da mensagem.

**O envio das medições acontece pelo Wi-Fi.** O cabo USB é usado para gravar o
programa na placa, fornecer alimentação quando aplicável e acompanhar as
mensagens do Monitor Serial. Abrir a Arduino IDE não inicia a API nem o banco.

No firmware, `ssid` e `password` configuram a rede. O campo `servidor` contém
o endereço completo da API e deve apontar para o IP do computador do backend.
O ESP32 e esse computador precisam conseguir se comunicar pela rede.

## 3. Recebimento e validação no backend

O FastAPI recebe a requisição e valida os quatro campos com Pydantic:

- Todos os campos devem estar presentes e conter números finitos.
- A umidade deve estar entre 0 e 100.
- A pressão e a luminosidade devem ser não negativas.
- A temperatura pode ser negativa, e zero é um valor válido nas medições.

Campos adicionais, valores nulos, strings com unidades e números inválidos
são rejeitados. A API responde com **HTTP 422** quando a requisição não segue
esse contrato.

Para uma requisição válida, o backend gera a data e a hora do registro em UTC.
O firmware não precisa enviar horário, identificador ou credenciais de acesso
no endpoint de ingestão do MVP.

## 4. Armazenamento no MongoDB

Cada requisição aceita origina um documento na coleção **`medicoes`** do banco
configurado no ambiente. O documento contém as quatro medições, o campo
`timestamp` e o identificador `_id` atribuído pelo MongoDB.

O `timestamp` é armazenado como uma data BSON. Ele representa o instante de
registro no servidor, com precisão de milissegundos. A coleção mantém o
histórico dos envios recebidos e possui um índice para consultar os mais recentes.

Após a inserção, o backend responde **HTTP 201**. O firmware reconhece esse
código e mostra `Medicao salva com sucesso!` no Monitor Serial. Se o MongoDB
estiver indisponível, a API responde com HTTP 503.

## 5. Consulta e apresentação no painel

O navegador consulta `/api/meteora`, uma rota do próprio Next.js. Essa rota
consulta `GET /api/station/latest` no FastAPI, recebe a última medição válida
e valida a resposta antes de entregá-la à interface.

O painel apresenta:

- Temperatura atual da estação.
- Umidade relativa.
- Pressão atmosférica.
- Luminosidade em lux.
- Horário da última medição.
- Mínima e máxima de temperatura observadas no dia da última leitura.

As mínimas e máximas são calculadas pelo backend usando somente medições
válidas armazenadas naquele dia, no fuso `America/Sao_Paulo`, até o instante
da leitura apresentada. Esses valores descrevem o histórico observado.

O painel consulta novas informações a cada **30 segundos**, enquanto a aba
está visível, e ao retornar para ela. O botão **Atualizar dados** permite uma
consulta manual. Os cards podem arredondar a apresentação; os valores recebidos
continuam disponíveis na API e no MongoDB.

## 6. Estados de operação e falhas

| Situação | Comportamento |
| --- | --- |
| Ainda não existe medição válida | O painel informa que está aguardando a estação |
| Há uma medição recente | Os cards apresentam os valores e o horário da leitura |
| A leitura tem mais de 90 segundos | O painel identifica a leitura como desatualizada |
| Uma consulta falha temporariamente | O painel mantém a última resposta válida disponível e informa a falha |
| O backend ou o MongoDB está indisponível | O painel informa dificuldade para atualizar e volta a tentar nas próximas consultas |
| Existem documentos antigos incompletos | Eles são preservados no banco e ignorados nas consultas de medições |

O firmware tenta restabelecer o Wi-Fi quando detecta desconexão. Ele não possui
fila de medições para reenvio: uma falha HTTP não cria um histórico local na
placa. Os ciclos seguintes realizam novas leituras e novas tentativas de envio.

## Condições para a operação completa

O ESP32 deve estar programado e alimentado, os sensores devem estar ligados
corretamente e a rede deve permitir acesso à API. MongoDB, backend e frontend
devem estar em execução, com os respectivos endereços configurados.

Com essas condições atendidas, a origem dos valores apresentados no painel
são os sensores da estação. Os componentes de hardware e a comunicação pela
rede precisam ser conferidos durante a instalação física.

Próxima leitura: [Arquitetura](ARQUITETURA.md) e
[Integração e dados](INTEGRACAO.md).
