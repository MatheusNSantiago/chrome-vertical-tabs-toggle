# Protocolo do host nativo

Cada mensagem é um objeto JSON enquadrado pelo protocolo Native Messaging do
Chrome: tamanho de 32 bits little-endian seguido do UTF-8.

`extension/native-host-contract.json` é a fonte canônica do nome e da descrição
usados pela extensão e pelos três instaladores. Seu `schema_version` deve ser
suportado antes da instalação.

## Pedidos

```json
{"command":"toggle"}
```

alterna o estado. Para garantir a barra recolhida:

```json
{"command":"collapse"}
```

`toggle` atua na janela ativa. `collapse` recolhe todas as janelas compatíveis
encontradas e é reenviado pela extensão durante a restauração inicial.

## Resposta de sucesso

```json
{"state":"collapsed"}
```

ou:

```json
{"state":"expanded"}
```

O estado indica o resultado da ação, não uma estimativa anterior.

## Falha

```json
{"error":"Chrome vertical tab toggle was not found"}
```

O leitor consome exatamente o cabeçalho e o payload de uma mensagem. Ele não
espera EOF, pois o navegador mantém o canal aberto enquanto aguarda a resposta.
