# Arquitetura

```text
atalho → extensão → Native Messaging → host do sistema → acessibilidade → Chrome
```

## Limites

`extension/` traduz o clique ou atalho em `toggle` e, na inicialização, agenda
`collapse` durante a restauração das janelas. Uma fila impede comandos
concorrentes no mesmo perfil. Ela não conhece processos, árvores de
acessibilidade ou idiomas.

`native-host/` contém três implementações independentes:

- `linux/` usa Python do sistema e AT-SPI;
- `macos/` usa Swift e AXUIElement;
- `windows/` usa C# e UI Automation.

Cada executável implementa o mesmo contrato de
[Native Messaging](docs/native-messaging.md). A seleção acontece naturalmente
quando o navegador encontra o host registrado pelo instalador do sistema; não
há factory em runtime.

`extension/native-host-contract.json` define a identidade do host. A extensão o
consome diretamente; os builds de macOS e Windows o incluem nos respectivos
instaladores, e o instalador Linux o lê do checkout. Não existem cópias
mantidas manualmente.

`native-host/resources/sidebar-labels.json` é o vocabulário comum dos três adapters.
`uv run update-sidebar-labels` o regenera a partir do HEAD do Chromium e grava
a revisão exata usada. `schema_version` protege a fronteira entre o gerador e
os três leitores. Os adapters decidem o controle e a ação nativos; não mantêm
traduções próprias.

`src/chrome_vertical_tabs_toggle/` contém apenas ferramentas de manutenção
executadas pelo uv. O host Linux não depende do ambiente virtual porque o
binding de AT-SPI pertence ao Python do sistema.

O instalador Linux copia o host para o diretório de dados do usuário antes de
registrá-lo. O manifesto nunca aponta para arquivos do checkout.

Os testes de contrato enviam uma mensagem enquadrada sem fechar `stdin`. Todo
host deve responder antes do EOF, independentemente da API de acessibilidade.

## Estado

`toggle` atua somente na janela ativa. `collapse` percorre todas as janelas
compatíveis encontradas, pois seu único caller é a inicialização da extensão.

O nome acessível do botão descreve a ação disponível:

- um rótulo de `collapse` significa que a barra está expandida;
- um rótulo de `expand` significa que a barra está recolhida.

O comando `collapse` não executa ação quando a barra já está recolhida. Após
invocar o botão, cada host observa a mudança do nome acessível antes de retornar
o estado resultante.
