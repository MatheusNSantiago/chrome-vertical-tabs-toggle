import os
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path

from chrome_vertical_tabs_toggle_linux.iterables import find

ACCESSIBILITY_FLAG = "--force-renderer-accessibility"


@dataclass(frozen=True)
class BrowserDistribution:
    name: str
    commands: tuple[str, ...]
    desktop_files: tuple[str, ...]
    profile_directory: str
    flags_file: str


@dataclass(frozen=True)
class BrowserInstallation:
    distribution: BrowserDistribution
    launcher: Path
    desktop_file: Path | None


def supported_distributions() -> tuple[BrowserDistribution, ...]:
    return (
        BrowserDistribution(
            name="Google Chrome",
            commands=("google-chrome-stable", "google-chrome"),
            desktop_files=("google-chrome.desktop", "google-chrome-stable.desktop"),
            profile_directory="google-chrome",
            flags_file="chrome-flags.conf",
        ),
        BrowserDistribution(
            name="Google Chrome Beta",
            commands=("google-chrome-beta",),
            desktop_files=("google-chrome-beta.desktop",),
            profile_directory="google-chrome-beta",
            flags_file="chrome-beta-flags.conf",
        ),
        BrowserDistribution(
            name="Google Chrome Dev",
            commands=("google-chrome-unstable",),
            desktop_files=("google-chrome-unstable.desktop",),
            profile_directory="google-chrome-unstable",
            flags_file="chrome-dev-flags.conf",
        ),
        BrowserDistribution(
            name="Google Chrome Canary",
            commands=("google-chrome-canary",),
            desktop_files=("google-chrome-canary.desktop",),
            profile_directory="google-chrome-canary",
            flags_file="chrome-canary-flags.conf",
        ),
        BrowserDistribution(
            name="Chromium",
            commands=("chromium", "chromium-browser"),
            desktop_files=("chromium.desktop", "chromium-browser.desktop"),
            profile_directory="chromium",
            flags_file="chromium-flags.conf",
        ),
    )


def xdg_configuration_home() -> Path:
    xdg_home = os.getenv("XDG_CONFIG_HOME")
    return Path(xdg_home) if xdg_home else Path.home() / ".config"


def browser_configuration_home() -> Path:
    chrome_home = os.getenv("CHROME_CONFIG_HOME")
    return Path(chrome_home) if chrome_home else xdg_configuration_home()


def data_home() -> Path:
    configured_home = os.getenv("XDG_DATA_HOME")
    return Path(configured_home) if configured_home else Path.home() / ".local/share"


def system_data_directories() -> tuple[Path, ...]:
    configured_directories = os.getenv(
        "XDG_DATA_DIRS",
        "/usr/local/share:/usr/share",
    )
    return tuple(Path(directory) for directory in configured_directories.split(":"))


def installed_browsers() -> tuple[BrowserInstallation, ...]:
    installations = [
        installation
        for distribution in supported_distributions()
        if (installation := find_browser(distribution)) is not None
    ]
    if not installations:
        raise FileNotFoundError("Google Chrome or Chromium was not found")
    return tuple(installations)


def find_browser(distribution: BrowserDistribution) -> BrowserInstallation | None:
    launchers = (shutil.which(command) for command in distribution.commands)
    launcher = find(launchers, lambda candidate: candidate is not None)
    if launcher is None:
        return
    return BrowserInstallation(
        distribution=distribution,
        launcher=Path(launcher).resolve(),
        desktop_file=find_desktop_file(distribution.desktop_files),
    )


def find_desktop_file(names: tuple[str, ...]) -> Path | None:
    search_directories = (data_home(), *system_data_directories())
    desktop_files = (
        directory / "applications" / name
        for directory in search_directories
        for name in names
    )
    return find(desktop_files, Path.exists)


def native_messaging_directory(installation: BrowserInstallation) -> Path:
    return (
        browser_configuration_home()
        / installation.distribution.profile_directory
        / "NativeMessagingHosts"
    )


def enable_accessibility(installation: BrowserInstallation) -> None:
    distribution = installation.distribution
    if launcher_supports_flags_file(installation):
        add_accessibility_flag(xdg_configuration_home() / distribution.flags_file)
        return
    if installation.desktop_file is None:
        raise RuntimeError(f"cannot persist accessibility for {distribution.name}")
    install_accessible_desktop_entry(installation, installation.desktop_file)


def launcher_supports_flags_file(installation: BrowserInstallation) -> bool:
    with installation.launcher.open("rb") as launcher:
        return installation.distribution.flags_file.encode() in launcher.read(64 * 1024)


def add_accessibility_flag(flags_path: Path) -> None:
    lines = flags_path.read_text().splitlines() if flags_path.exists() else []
    if ACCESSIBILITY_FLAG in (line.strip() for line in lines):
        return

    flags_path.parent.mkdir(parents=True, exist_ok=True)
    flags_path.write_text("\n".join([*lines, ACCESSIBILITY_FLAG]) + "\n")


def install_accessible_desktop_entry(
    installation: BrowserInstallation,
    desktop_file: Path,
) -> None:
    distribution = installation.distribution
    integration_directory = data_home() / "chrome-vertical-tabs-toggle"
    wrapper_path = integration_directory / distribution.profile_directory
    user_desktop_path = data_home() / "applications" / desktop_file.name

    integration_directory.mkdir(parents=True, exist_ok=True)
    wrapper_path.write_text(
        "#!/bin/sh\n"
        f"exec {shlex.quote(str(installation.launcher))} "
        f'{ACCESSIBILITY_FLAG} "$@"\n'
    )
    wrapper_path.chmod(0o755)

    user_desktop_path.parent.mkdir(parents=True, exist_ok=True)
    user_desktop_path.write_text(
        desktop_file_with_launcher(desktop_file.read_text(), wrapper_path)
    )
    patch_autostart_entry(desktop_file.name, wrapper_path)


def patch_autostart_entry(desktop_file_name: str, wrapper_path: Path) -> None:
    autostart_file = xdg_configuration_home() / "autostart" / desktop_file_name
    if not autostart_file.exists():
        return
    contents = desktop_file_with_launcher(autostart_file.read_text(), wrapper_path)
    autostart_file.write_text(contents)


def desktop_file_with_launcher(contents: str, launcher: Path) -> str:
    lines = [
        replace_desktop_command(line, launcher) if line.startswith("Exec=") else line
        for line in contents.splitlines()
    ]
    return "\n".join(lines) + "\n"


def replace_desktop_command(line: str, launcher: Path) -> str:
    arguments = line.removeprefix("Exec=").partition(" ")[2]
    if not arguments:
        return f"Exec={launcher}"
    return f"Exec={launcher} {arguments}"
