import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from chrome_vertical_tabs_toggle_linux_installation.browsers import (
    BrowserDistribution,
    BrowserInstallation,
    add_accessibility_flag,
    desktop_file_with_launcher,
    enable_accessibility,
)
from chrome_vertical_tabs_toggle_linux_installation.native_host import (
    NativeHostContract,
    deploy_native_host,
    read_native_host_contract,
    register_native_host,
)


class InstallTest(unittest.TestCase):
    def test_reads_the_canonical_native_host_contract(self) -> None:
        contract_path = (
            Path(__file__).parents[2] / "extension/native-host-contract.json"
        )

        contract = read_native_host_contract(contract_path)

        self.assertEqual(contract.name, "dev.matheus.chrome_vertical_tabs")
        self.assertEqual(
            contract.description,
            "Chrome Vertical Tabs Toggle native host",
        )

    def test_deploys_an_independent_native_host(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_directory = Path(__file__).parents[2] / "native-host/linux"
            labels_path = source_directory.parent / "resources/sidebar-labels.json"
            stale_module = (
                root
                / "chrome-vertical-tabs-toggle/native-host/linux"
                / "chrome_vertical_tabs_toggle_linux/stale.py"
            )
            stale_module.parent.mkdir(parents=True)
            stale_module.write_text("")

            host_path = deploy_native_host(
                source_directory,
                labels_path,
                root,
            )

            deployed_package = host_path.parent / "chrome_vertical_tabs_toggle_linux"

            self.assertTrue(host_path.is_file())
            self.assertTrue(
                (host_path.parent.parent / "resources/sidebar-labels.json").is_file()
            )
            self.assertTrue((deployed_package / "atspi.py").is_file())
            self.assertFalse(stale_module.exists())
            self.assertNotEqual(host_path.parent, source_directory)

    def test_preserves_extension_ids_registered_by_previous_installations(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            manifest_directory = Path(temporary_directory)
            contract = NativeHostContract(
                name="dev.matheus.chrome_vertical_tabs",
                description="Native host",
            )
            host_path = manifest_directory / "main.py"
            register_native_host(
                manifest_directory,
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                contract,
                host_path,
            )
            register_native_host(
                manifest_directory,
                "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                contract,
                host_path,
            )

            manifest = json.loads(
                (
                    manifest_directory / "dev.matheus.chrome_vertical_tabs.json"
                ).read_text()
            )

        self.assertEqual(
            manifest["allowed_origins"],
            [
                "chrome-extension://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/",
                "chrome-extension://bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/",
            ],
        )

    def test_adds_the_accessibility_flag_without_replacing_existing_flags(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            flags_path = Path(temporary_directory) / "chrome-flags.conf"
            flags_path.write_text("# My flag\n--disable-features=Foo")

            add_accessibility_flag(flags_path)
            add_accessibility_flag(flags_path)

            self.assertEqual(
                flags_path.read_text(),
                "# My flag\n--disable-features=Foo\n--force-renderer-accessibility\n",
            )

    def test_installs_a_desktop_launcher_when_the_flags_file_is_not_supported(
        self,
    ) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            installation = browser_installation(root, profile_directory="chromium")
            with (
                patch(
                    "chrome_vertical_tabs_toggle_linux_installation."
                    "browsers.xdg_configuration_home",
                    return_value=root / ".config",
                ),
                patch(
                    "chrome_vertical_tabs_toggle_linux_installation.browsers.data_home",
                    return_value=root / ".local/share",
                ),
            ):
                enable_accessibility(installation)

            wrapper = root / ".local/share/chrome-vertical-tabs-toggle/chromium"
            user_desktop = root / ".local/share/applications/chromium.desktop"
            wrapper_contents = wrapper.read_text()
            desktop_contents = user_desktop.read_text()

        self.assertEqual(
            wrapper_contents,
            f'#!/bin/sh\nexec {installation.launcher} --force-renderer-accessibility "$@"\n',
        )
        self.assertEqual(
            desktop_contents,
            f"[Desktop Entry]\nName=Chrome\nExec={wrapper} %U\n",
        )

    def test_replaces_every_desktop_action_launcher(self) -> None:
        wrapper = Path("/home/user/.local/share/chrome-toggle/chromium")
        contents = (
            "[Desktop Entry]\n"
            "Exec=/usr/bin/chromium %U\n"
            "[Desktop Action new-private-window]\n"
            "Exec=/usr/bin/chromium --incognito\n"
        )

        self.assertEqual(
            desktop_file_with_launcher(contents, wrapper),
            (
                "[Desktop Entry]\n"
                f"Exec={wrapper} %U\n"
                "[Desktop Action new-private-window]\n"
                f"Exec={wrapper} --incognito\n"
            ),
        )


def browser_installation(root: Path, profile_directory: str) -> BrowserInstallation:
    launcher = root / profile_directory
    desktop_file = root / f"{profile_directory}.desktop"
    launcher.write_text("#!/bin/sh\n")
    desktop_file.write_text(
        f"[Desktop Entry]\nName=Chrome\nExec=/usr/bin/{profile_directory} %U\n"
    )
    distribution = BrowserDistribution(
        name="Chrome",
        commands=(profile_directory,),
        desktop_files=(desktop_file.name,),
        profile_directory=profile_directory,
        flags_file=f"{profile_directory}-flags.conf",
    )
    return BrowserInstallation(distribution, launcher, desktop_file)


if __name__ == "__main__":
    unittest.main()
