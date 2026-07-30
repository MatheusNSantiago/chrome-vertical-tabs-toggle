<p align="center">
  <img src="assets/icon.svg" width="112" alt="Ícone do Chrome Vertical Tabs Toggle">
</p>

# Chrome Vertical Tabs Toggle

Recolha ou expanda a barra nativa de abas verticais do Chrome com um atalho ou
um clique na barra de ferramentas.

[English](README.md)

![Barra de abas verticais sendo alternada com Ctrl+Shift+Y](assets/demo.gif)

- Alterna a barra da janela ativa do Chrome.
- Recolhe as barras compatíveis quando o Chrome inicia.
- Funciona no Linux, macOS e Windows.

## Instalação

Extensões não podem controlar a interface do próprio Chrome. Por isso, o
projeto possui duas partes: a extensão descompactada recebe o atalho, e um host
nativo pressiona o botão da barra lateral.

### 1. Instale a extensão

1. Baixe `chrome-vertical-tabs-toggle-extension-*.zip` na
   [release mais recente](https://github.com/MatheusNSantiago/chrome-vertical-tabs-toggle/releases/latest).
2. Extraia o arquivo em um diretório permanente.
3. Abra `chrome://extensions`.
4. Ative o **Modo do desenvolvedor**.
5. Selecione **Carregar sem compactação** e escolha o diretório extraído.

### 2. Instale o host nativo

Baixe o arquivo do seu sistema operacional na mesma release.

#### Linux

Extraia `chrome-vertical-tabs-toggle-linux-*.tar.gz`, entre no diretório e
execute:

```sh
native-host/linux/install.py
```

Encerre todos os processos do Chrome ou Chromium e abra o navegador novamente.

Requer Python 3.10+, PyGObject e AT-SPI. Pacotes Snap e Flatpak não são
suportados.

#### macOS

Extraia `chrome-vertical-tabs-toggle-macos-*.zip` e execute:

```sh
./install.sh
```

Em **Ajustes do Sistema → Privacidade e Segurança → Acessibilidade**, habilite
`Chrome Vertical Tabs Toggle.app` e reinicie o Chrome.

#### Windows

Extraia `chrome-vertical-tabs-toggle-windows-*.zip` e execute:

```powershell
.\install.cmd
```

Reinicie o Chrome após a instalação.

### 3. Ative as abas verticais

Caso o Chrome ainda não mostre a opção de abas verticais:

1. Abra `chrome://flags/#vertical-tabs`.
2. Habilite **Vertical tabs** e reinicie o Chrome.
3. Clique com o botão direito na barra de abas e selecione **Mover abas para a
   lateral**.

## Uso

| Ação | Linux e Windows | macOS |
| --- | --- | --- |
| Alternar a barra ativa | `Ctrl+Shift+Y` | `Command+Shift+Y` |
| Alterar o atalho | `chrome://extensions/shortcuts` | `chrome://extensions/shortcuts` |

Clicar no ícone da extensão executa a mesma ação. O atalho funciona enquanto o
Chrome está em foco.

## Compatibilidade

| Sistema | Navegadores suportados |
| --- | --- |
| Linux | Pacotes nativos do Google Chrome Stable, Beta, Dev, Canary; Chromium |
| macOS 13+ | Google Chrome Stable, Beta, Dev, Canary; Chromium |
| Windows 10 e 11 | Google Chrome; Chromium |

Outros navegadores baseados no Chromium ainda não são suportados.

## Permissões

A extensão solicita apenas `nativeMessaging`. Ela não possui acesso a sites e
não pode ler o conteúdo das páginas nem o histórico por meio de uma permissão
de extensão.

## Solução de problemas

### O host nativo não foi encontrado

O Chrome identifica uma extensão descompactada a partir do diretório de
instalação. Se a extensão foi movida ou carregada novamente de outro diretório,
copie o ID atual em `chrome://extensions`, execute outra vez o instalador do
host nativo e reinicie todos os processos do Chrome.

### O botão das abas verticais não foi encontrado

Confirme que as abas verticais estão habilitadas e visíveis na janela ativa. No
Linux, confirme também que o Chrome foi completamente reiniciado após executar
o instalador.

### O atalho não faz nada

Abra `chrome://extensions/shortcuts` e confirme que o atalho está atribuído e
não conflita com outra extensão. O Chrome deve estar em foco.

### O macOS solicita acesso à Acessibilidade

Habilite `Chrome Vertical Tabs Toggle.app` em **Ajustes do Sistema → Privacidade
e Segurança → Acessibilidade**. O aplicativo instalado fica em:

```text
~/Library/Application Support/Chrome Vertical Tabs Toggle/
```

## Build a partir do código-fonte

Clone o repositório, carregue [`extension/`](extension) em
`chrome://extensions` e então compile ou instale o host:

```sh
# Linux
native-host/linux/install.py

# macOS
native-host/macos/build.sh
native-host/macos/dist/install.sh
```

```powershell
# Windows
.\native-host\windows\build.ps1
.\native-host\windows\dist\windows\install.cmd
```

O build do macOS requer as Command Line Tools do Xcode. O build do Windows
requer o SDK .NET.

## Desenvolvimento

Instale o projeto Python e execute a validação:

```sh
uv sync
uv run ruff check
uv run python -m unittest discover -s tests
```

Os rótulos acessíveis da barra são gerados a partir das traduções oficiais do
Chromium:

```sh
uv run update-sidebar-labels
```

Os limites entre os módulos estão em [ARCHITECTURE.md](ARCHITECTURE.md), e o
protocolo nativo está documentado em
[docs/native-messaging.md](docs/native-messaging.md).
