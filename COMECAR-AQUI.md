# Executar o Meteora e testar sem sensores

Este roteiro é para Windows. **Não é preciso conectar o ESP32 por USB para
testar o site, a API e o MongoDB.** O simulador ocupa o lugar do ESP32 e envia
as mesmas quatro medições pela mesma rota HTTP.

```text
ESP32 OU simulador → backend na porta 8000 → MongoDB / meteora / medicoes
                          ↑
                 frontend na porta 3000
```

## 1. Preparar o computador, uma vez

Instale Python 3.12 ou superior (marque **Add python.exe to PATH** no instalador),
Node.js 22.18 ou superior e MongoDB Community como serviço do Windows. MongoDB
Compass é opcional e serve para visualizar os dados.

Copie/clone o projeto completo para esse computador. Não copie `.venv` ou
`node_modules` de outro computador: o passo seguinte cria as dependências locais.

Abra a pasta `scripts/` dentro do projeto: os arquivos `.cmd` estão reunidos ali.
Os comandos PowerShell deste guia partem da raiz do projeto.
Clique duas vezes em **`scripts/preparar.cmd`** e espere aparecer **Preparacao concluida**.
Esse passo precisa de internet e pode demorar na primeira execução.

Ele instala as dependências e cria estes arquivos, sem sobrescrever configurações
que já existam:

| Arquivo local | O que configura |
| --- | --- |
| `backend/.env` | Conexão da API com o MongoDB |
| `frontend/.env.local` | Endereço da API consultada pelo site |

O banco local sem autenticação fica em `backend/.env`:

```dotenv
MONGODB_URI=mongodb://127.0.0.1:27017
MONGODB_DATABASE=meteora
```

O frontend fica em `frontend/.env.local`:

```dotenv
METEORA_STATION_URL=http://127.0.0.1:8000/api/station/latest
METEORA_FORECAST_URL=
METEORA_API_TOKEN=
```

URI e nome do banco são obrigatórios no ambiente; o código Python não define
valores padrão para eles. Os arquivos locais não vão para o Git. Por isso, em
outro computador, execute `scripts/preparar.cmd` novamente e ajuste os arquivos locais.
Reinicie backend e frontend se editar os respectivos arquivos `.env`.

## 2. Abrir o backend

Clique duas vezes em **`scripts/iniciar-backend.cmd`** e mantenha a janela aberta.

O comando verifica o MongoDB e mostra algo como:

```text
MongoDB conectado. Banco: meteora; colecao: medicoes; registros: 0.
```

O número de registros pode ser diferente. A criação da coleção e do índice é
automática; não é necessário criar campos manualmente no Compass.

Abra <http://localhost:8000/api/health/> no navegador. O resultado esperado é:

```json
{"status":"ok","database":"ok"}
```

Se isso não funcionar, resolva essa etapa antes de conectar o ESP32. Em
<http://localhost:8000/docs> você encontra a documentação interativa da API.

## 3. Abrir o frontend

Clique duas vezes em **`scripts/iniciar-frontend.cmd`** e mantenha essa segunda janela
aberta. Quando aparecer que o servidor está pronto, abra:

**<http://localhost:3000>**

Se ainda não houver medições, o site informa que está aguardando a estação.
O painel mostra temperatura, umidade, pressão e luminosidade, além dos extremos
observados do dia. Chuva, sensor de ar, previsões e horários solares foram
retirados da tela porque não são fornecidos pelos sensores atuais.

## 4. Colocar dados fictícios no MongoDB e no site

Com as duas janelas anteriores abertas, clique duas vezes em **`scripts/simular-dados.cmd`**.

Uma terceira janela enviará uma medição a cada 10 segundos. Ela mostrará:

```text
SIMULACAO: valores ficticios enviados pelo mesmo endpoint do ESP32.
HTTP 201 | id=... | {"temperatura": 26.0, "umidade": 73.0, "pressao": 1013.0, "luminosidade": 350.0}
```

**HTTP 201 significa que o backend recebeu e gravou a medição.** No site, clique
em **Atualizar dados** ou espere até 30 segundos. Confira temperatura, umidade,
pressão e luminosidade em lux. Esses números são fictícios enquanto o simulador
estiver em execução.

Você pode conferir os mesmos dados diretamente nestes endereços:

- Última medição: <http://localhost:8000/api/medicoes/ultima/>
- Últimas 5 medições: <http://localhost:8000/api/medicoes/?limit=5>
- Resposta usada pelo frontend: <http://localhost:8000/api/station/latest>
- Resposta do próprio Next.js: <http://localhost:3000/api/meteora>

Para parar, pressione **Ctrl+C na janela do simulador**. Os dados permanecem no
banco depois que você fecha o programa. Após 90 segundos sem nova leitura, o
site sinaliza a medição como desatualizada; isso é esperado.

Para enviar só três medições, abra PowerShell na raiz do projeto e execute:

```powershell
.\scripts\simular-dados.cmd --count 3 --interval 2
```

### Ver os dados no MongoDB Compass

1. Abra o Compass e conecte em `mongodb://127.0.0.1:27017`, sem usuário e senha.
2. Abra o banco **meteora**, depois a coleção **medicoes**.
3. Na aba **Documents**, clique em **Refresh**. Na opção **Sort**, informe
   `{ "timestamp": -1 }` para ver as mais novas primeiro.
4. Confira `temperatura`, `umidade`, `pressao`, `luminosidade` e `timestamp`.
   O timestamp é uma data BSON em UTC; horários na interface usam Brasília.

O `id` retornado pela API corresponde ao `_id` do documento no Compass.

### Remover apenas os dados fictícios deste simulador

Primeiro pare o simulador com Ctrl+C. Depois execute **`scripts/limpar-dados-simulados.cmd`**.

O simulador guarda os ids que criou em `backend/.cache/simulacoes/`. A limpeza
remove somente esses ids, na mesma configuração de banco. Medições que já
existiam e futuras leituras reais são preservadas. Não apague essa pasta antes
de limpar e não altere a URI/nome do banco entre simular e limpar. Arquivos de
outra configuração são ignorados. Dados inseridos manualmente pelo Swagger ou
Compass não fazem parte dessa limpeza.

Depois, clique em Atualizar dados no site. Se não restarem medições, ele volta
ao estado de espera. Pare o simulador antes de começar o teste dos sensores
reais para não misturar envios dos dois.

## 5. Preparar o ESP32 no computador da outra pessoa

O arquivo do Arduino tem extensão **`.ino`**:
`firmware/sketch_oct31a/sketch_oct31a.ino`. Ele foi mantido no estado original.
Nenhuma placa é necessária para os passos 1 a 4. As instruções abaixo ficam
para a pessoa que fará o teste físico futuramente.

O mais simples é executar **todo o projeto no computador que estará junto dos
sensores**: MongoDB, backend e frontend. A outra pessoa segue os passos 1 a 4
primeiro, mesmo sem USB. Depois, quando o USB funcionar, faz os passos abaixo.
Também é possível manter o backend em outro computador, desde que esteja na
mesma rede e acessível pelo ESP32. Computadores em redes diferentes não se
alcançam usando apenas esses endereços locais.

### Descobrir e testar o endereço do backend

No computador que executa `scripts/iniciar-backend.cmd`, abra o Prompt de Comando e
execute `ipconfig`. Procure o **Endereço IPv4** da conexão Wi-Fi/Ethernet em uso,
por exemplo `192.168.1.50`. Não use um endereço de VPN ou adaptador desconectado.

No outro computador ou celular, conectado à mesma rede, abra:

```text
http://192.168.1.50:8000/api/health/
```

Substitua o IP pelo que você encontrou. Precisa aparecer o JSON com `ok`.
Se necessário, permita o Python no Firewall do Windows na rede privada para
acessar a porta 8000. Redes de convidados podem impedir comunicação entre
dispositivos. Para abrir o site em outro aparelho, use `http://192.168.1.50:3000`
e permita também o Node.js na rede privada.

**A URI do MongoDB continua `127.0.0.1:27017` no computador do backend.**
O ESP32 se conecta à API na porta 8000; ele não acessa o MongoDB diretamente.
Quando frontend e backend estão no mesmo computador, a URL em `.env.local`
também continua `127.0.0.1:8000`, mesmo se você abrir o site pelo celular.

### Configurar e enviar o firmware

1. Instale/abra a Arduino IDE e o pacote de placas **esp32 by Espressif Systems**.
2. No gerenciador de bibliotecas, instale **DHT sensor library by Adafruit**,
   **Adafruit Unified Sensor**, **Adafruit BMP280 Library**, **Adafruit BusIO** e
   **BH1750 by Christopher Laws**. `WiFi`, `HTTPClient` e `Wire` acompanham o
   pacote da placa ESP32.
3. Quando houver placa disponível, abra `sketch_oct31a.ino`. A pessoa responsável
   deverá conferir estes três campos de configuração de rede já existentes no
   início do arquivo. Exemplo para o computador de IP `192.168.1.50`:

```cpp
const char* ssid = "NOME_DO_WIFI";
const char* password = "SENHA_DO_WIFI";
const char* servidor = "http://192.168.1.50:8000/api/medicoes/";
```

4. Nesse teste futuro, use Wi-Fi, senha e IP dessa rede. Mantenha a rota final
   `/api/medicoes/`. Não coloque `localhost`, `127.0.0.1` ou `0.0.0.0` nessa URL.
5. Conecte o ESP32 com um cabo USB que transmita dados, selecione o modelo da
   placa e a porta correspondente na Arduino IDE e envie o programa.
6. Abra o **Monitor Serial em 115200 baud**. Confira `Wi-Fi conectado`, o estado
   dos sensores e, a cada 10 segundos, `Codigo HTTP: 201` seguido de
   `Medicao salva com sucesso!`.
7. Confira a nova medição no site e no Compass, como fez com os dados fictícios.

O firmware mantém DHT22 no pino 4 e I²C nos pinos 21 (SDA) e 22 (SCL),
BMP280 em 0x76/0x77. Leituras inválidas cancelam o envio. O teste físico e a
compilação com a placa/bibliotecas escolhidas precisam ser feitos na Arduino IDE.

## Quando algo não funcionar

| O que aparece | O que conferir |
| --- | --- |
| Python ou Node não encontrado | Reabra o terminal após instalar; execute `scripts/preparar.cmd` |
| Não foi possível acessar MongoDB | Abra Serviços do Windows, encontre MongoDB e inicie; confira `backend/.env` |
| Porta 8000 ou 3000 em uso | Feche a janela anterior desse servidor; mantenha uma instância de cada |
| Simulador não acessa a API | Abra `scripts/iniciar-backend.cmd` antes de `scripts/simular-dados.cmd` |
| HTTP 503 | A API está acessível, mas o MongoDB não está disponível |
| HTTP 422 | Confira os quatro números do payload; não use texto, null ou valores inválidos |
| Site sem dados apesar do HTTP 201 | Confira `.env.local`, reinicie o frontend e abra `/api/meteora` |
| Documento no Compass, mas site aguardando leitura | Documentos sem `timestamp` BSON ou com medições incompletas são preservados e ignorados. Use `scripts/simular-dados.cmd` para gravar uma medição completa pela API |
| Funciona no PC, mas o ESP32 não alcança | Confira IP, mesma rede, teste de `/api/health/` em outro aparelho e firewall |
| Serial sem mostrar Wi-Fi conectado | A pessoa com a placa deve conferir nome/senha/rede nos campos existentes do firmware |
| Leitura inválida no Serial | Confira ligação, alimentação e presença dos quatro valores dos sensores |
| Não há chuva ou previsão na tela | Esperado: o painel mostra somente as medições disponíveis no firmware |

Para encerrar o projeto, use Ctrl+C nas janelas do simulador, frontend e backend.
O serviço MongoDB pode continuar em execução. Para abrir novamente no dia
seguinte, execute os dois arquivos `scripts/iniciar-*.cmd`; não é preciso preparar tudo
ou instalar as dependências novamente.

Para executar a validação completa, use `scripts/validar.cmd`. Ela confere o
contrato do `.ino`, testa a API com MongoDB real e consulta o Next.js usando
um banco e servidores temporários. Não usa placa física nem altera o banco
do projeto. O resultado fica em `backend/.cache/ultima-validacao.json`.

Visão geral: [README.md](README.md). Detalhes da API e testes automatizados:
[backend/README.md](backend/README.md).
