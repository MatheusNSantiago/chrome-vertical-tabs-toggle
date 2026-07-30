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
quando o navegador encontra o host registrado pelo instalador do sistema.

`extension/native-host-contract.json` define as identidades da extensão e do
host. A extensão o consome diretamente; os builds de macOS e Windows o incluem
nos respectivos instaladores, e o instalador Linux o lê do checkout.

`native-host/resources/sidebar-labels.json` é o vocabulário comum dos três adapters.
`uv run update-sidebar-labels` o regenera a partir do HEAD do Chromium e grava
a revisão exata usada. `schema_version` protege a fronteira entre o gerador e
os três leitores. Os adapters decidem o controle e a ação nativos; não mantêm
traduções próprias.

O instalador Linux copia o host para o diretório de dados do usuário antes de
registrá-lo.

## Estado

`toggle` atua somente na janela ativa. `collapse` percorre todas as janelas
compatíveis encontradas, pois seu único caller é a inicialização da extensão.

O nome acessível do botão descreve a ação disponível:

- um rótulo de `collapse` significa que a barra está expandida;
- um rótulo de `expand` significa que a barra está recolhida.

O comando `collapse` não executa ação quando a barra já está recolhida. Após
invocar o botão, cada host observa a mudança do nome acessível antes de retornar
o estado resultante.
