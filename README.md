# Chrome Vertical Tabs Toggle

Atalho para recolher ou expandir a barra nativa de abas verticais do Chrome e
do Chromium.

A extensão MV3 recebe o clique ou atalho. Um host nativo aciona o botão pela
API de acessibilidade do sistema: AT-SPI no Linux, AXUIElement no macOS e UI
Automation no Windows. Não há reconhecimento de imagem nem clique por
coordenada.

Os rótulos acessíveis seguem o idioma do navegador. O arquivo
`native-host/resources/sidebar-labels.json` é gerado das traduções oficiais do Chromium:

```sh
uv run update-sidebar-labels
```

## Extensão

Carregue `extension/` em `chrome://extensions` com o modo de desenvolvedor
ativo e copie o identificador mostrado. O instalador do host recebe esse
identificador.

O atalho padrão é `Ctrl+Shift+Y`, ou `Command+Shift+Y` no macOS. Ele também
pode ser alterado em `chrome://extensions/shortcuts` e funciona enquanto o
Chrome está em foco.

## Linux

```sh
native-host/linux/install.py <identificador-da-extensão>
```

O instalador detecta Google Chrome Stable, Beta, Dev, Canary e Chromium
instalados como pacotes nativos. Para cada instalação, ele:

- copia o host para `~/.local/share/chrome-vertical-tabs-toggle/`;
- registra o host no diretório de perfil correspondente;
- usa o arquivo de flags quando o launcher oferece esse recurso;
- caso contrário, cria um desktop entry do usuário que inicia o navegador com
  `--force-renderer-accessibility`.

Reinicie todos os processos do navegador após instalar. Snap e Flatpak não são
suportados porque seus sandboxes não permitem registrar e executar este host
nativo pelo mesmo mecanismo.

## macOS

```sh
native-host/macos/build.sh
native-host/macos/dist/install.sh <identificador-da-extensão>
```

O build requer as Command Line Tools do Xcode. O instalador registra o app para
os canais do Google Chrome e para Chromium, abre a tela de Acessibilidade e
solicita a autorização necessária no primeiro uso.

## Windows

```powershell
.\native-host\windows\build.ps1
.\native-host\windows\dist\windows\install.cmd <identificador-da-extensão>
```

O build usa o SDK .NET e gera um executável AnyCPU sobre o .NET Framework
incluído no Windows. O host acessa UI Automation diretamente, sem bibliotecas
adicionais. O instalador o registra para Google Chrome e Chromium no perfil do
usuário.

## Validação

```sh
uv run python -m unittest discover -s tests
```

Os limites entre os módulos estão em [ARCHITECTURE.md](ARCHITECTURE.md).
