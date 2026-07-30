<p align="center">
  <img src="assets/icon.svg" width="112" alt="Chrome Vertical Tabs Toggle icon">
</p>

# Chrome Vertical Tabs Toggle

Collapse or expand Chrome's native vertical tab sidebar with a keyboard shortcut
or a toolbar click.

[Português (Brasil)](README.pt-BR.md)

![Chrome vertical tab sidebar being toggled with Ctrl+Shift+Y](assets/demo.gif)

- Toggles the sidebar in the active Chrome window.
- Collapses compatible sidebars when Chrome starts.
- Supports Linux, macOS, and Windows.
- Uses the operating system's accessibility API, without image matching or
  coordinate-based clicks.

## Install

Chrome extensions cannot control the browser's own interface. This project
therefore has two parts: the unpacked extension receives the shortcut, and a
native host presses Chrome's sidebar button.

### 1. Install the extension

1. Download `chrome-vertical-tabs-toggle-extension-*.zip` from the
   [latest release](https://github.com/MatheusNSantiago/chrome-vertical-tabs-toggle/releases/latest).
2. Extract it to a permanent directory.
3. Open `chrome://extensions`.
4. Enable **Developer mode**.
5. Select **Load unpacked** and choose the extracted directory.
6. Copy the extension ID shown by Chrome. The native host installer needs it.

### 2. Install the native host

Download the archive for your operating system from the same release.

#### Linux

Extract `chrome-vertical-tabs-toggle-linux-*.tar.gz`, enter its directory, and
run:

```sh
native-host/linux/install.py <extension-id>
```

Exit every Chrome or Chromium process and open the browser again.

The installer supports native packages of Google Chrome Stable, Beta, Dev,
Canary, and Chromium. Snap and Flatpak packages are not supported because their
sandboxes prevent this native host integration.

#### macOS

Extract `chrome-vertical-tabs-toggle-macos-*.zip` and run:

```sh
./install.sh <extension-id>
```

In **System Settings → Privacy & Security → Accessibility**, enable
`Chrome Vertical Tabs Toggle.app`, then restart Chrome. The release contains a
universal executable for Apple silicon and Intel Macs.

#### Windows

Extract `chrome-vertical-tabs-toggle-windows-*.zip` and run:

```powershell
.\install.cmd <extension-id>
```

Restart Chrome after installation.

### 3. Enable vertical tabs

If Chrome does not already show the vertical-tabs option:

1. Open `chrome://flags/#vertical-tabs`.
2. Enable **Vertical tabs** and restart Chrome.
3. Right-click the tab bar and select **Move tabs to the side**.

## Use

| Action | Linux and Windows | macOS |
| --- | --- | --- |
| Toggle the active sidebar | `Ctrl+Shift+Y` | `Command+Shift+Y` |
| Change the shortcut | `chrome://extensions/shortcuts` | `chrome://extensions/shortcuts` |

Clicking the extension's toolbar icon performs the same action. The shortcut
works while Chrome is focused.

When Chrome starts, the extension retries briefly while browser windows are
being restored and collapses every compatible vertical-tab sidebar it finds.

## Compatibility

| System | Supported browsers | Native requirement |
| --- | --- | --- |
| Linux | Google Chrome Stable, Beta, Dev, Canary; Chromium | Python 3.10+, PyGObject, and AT-SPI |
| macOS 13+ | Google Chrome Stable, Beta, Dev, Canary; Chromium | Accessibility permission |
| Windows 10 and 11 | Google Chrome; Chromium | .NET Framework 4.6.2 or newer |

Chrome-derived browsers with different application identifiers, executable
names, or native-messaging directories are not currently detected.

## Permissions

The extension requests only `nativeMessaging`. It has no site access and cannot
read page contents or browsing history through an extension permission.

Messages to the native host contain one of two commands:

```json
{"command": "toggle"}
{"command": "collapse"}
```

The host uses AT-SPI on Linux, AXUIElement on macOS, or UI Automation on Windows
to find Chrome's accessible **Expand tabs** or **Collapse tabs** button and
invoke its native press action.

```text
shortcut or toolbar click
          ↓
Chrome extension
          ↓ Native Messaging
native host
          ↓ accessibility API
Chrome's vertical-tabs button
```

## Troubleshooting

### The native host was not found

Chrome identifies an unpacked extension from its installation directory. If
the extension was moved or loaded again from another directory, copy its
current ID from `chrome://extensions` and rerun the native host installer.
Restart every Chrome process afterwards.

### The vertical-tab toggle was not found

Confirm that vertical tabs are enabled and visible in the active Chrome window.
On Linux, also confirm that Chrome was completely restarted after running the
installer; the installer enables the accessibility tree on the browser
launcher.

### The shortcut does nothing

Open `chrome://extensions/shortcuts` and confirm that the shortcut is assigned
and not conflicting with another extension. Chrome must be focused.

### macOS asks for Accessibility access

Enable `Chrome Vertical Tabs Toggle.app` in **System Settings → Privacy &
Security → Accessibility**. The installed app is located at:

```text
~/Library/Application Support/Chrome Vertical Tabs Toggle/
```

## Build from source

Clone the repository and load [`extension/`](extension) through
`chrome://extensions`. Copy its extension ID, then build or install the host:

```sh
# Linux
native-host/linux/install.py <extension-id>

# macOS
native-host/macos/build.sh
native-host/macos/dist/install.sh <extension-id>
```

```powershell
# Windows
.\native-host\windows\build.ps1
.\native-host\windows\dist\windows\install.cmd <extension-id>
```

The macOS build requires the Xcode Command Line Tools. The Windows build
requires the .NET SDK.

## Development

Install the Python project and run its validation:

```sh
uv sync
uv run ruff check
uv run python -m unittest discover -s tests
```

Accessible sidebar labels are generated from Chromium's official translations:

```sh
uv run update-sidebar-labels
```

Pushing a `v*` tag runs validation on Linux, macOS, and Windows, builds the
platform hosts, packages the unpacked extension, and publishes the four
artifacts in a GitHub release.

The module boundaries are described in [ARCHITECTURE.md](ARCHITECTURE.md), and
the native protocol is documented in
[docs/native-messaging.md](docs/native-messaging.md).
