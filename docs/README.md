# Documentação do Meteora

O Meteora utiliza as leituras dos sensores conectados ao ESP32 para acompanhar
temperatura, umidade, pressão atmosférica e luminosidade. O backend recebe e
armazena essas medições, e o painel apresenta a última leitura disponível.

## Por onde começar

| Documento | O que explica |
| --- | --- |
| [Funcionamento do projeto](FUNCIONAMENTO.md) | O caminho da medição, desde o sensor até a tela, e o comportamento durante a operação |
| [Arquitetura](ARQUITETURA.md) | Responsabilidades do firmware, backend, MongoDB e frontend |
| [Integração e dados](INTEGRACAO.md) | Campos, unidades, rotas, horários e comunicação entre as partes |

A leitura recomendada começa por **Funcionamento do projeto**. Os demais
documentos detalham como esse funcionamento foi implementado.

## Guias de execução

- [README da raiz](../README.md): instalação, estrutura e comandos principais.
- [Começar aqui](../COMECAR-AQUI.md): roteiro de configuração e operação no Windows.
- [Backend](../backend/README.md): configuração e documentação técnica da API.
- [Frontend](../frontend/README.md): organização e execução do painel.

Os documentos desta pasta descrevem o funcionamento implementado para a
operação com sensores. A coleta depende do ESP32 programado, sensores ligados,
rede configurada e serviços em execução.
