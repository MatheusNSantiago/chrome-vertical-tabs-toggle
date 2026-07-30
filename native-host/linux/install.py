#!/usr/bin/env python3

from pathlib import Path

from chrome_vertical_tabs_toggle_linux_installation.browsers import (
    data_home,
    enable_accessibility,
    installed_browsers,
    native_messaging_directory,
)
from chrome_vertical_tabs_toggle_linux_installation.native_host import (
    deploy_native_host,
    read_native_host_contract,
    register_native_host,
)


def main() -> None:
    source_directory = Path(__file__).resolve().parent
    project_directory = source_directory.parents[1]
    contract = read_native_host_contract(
        project_directory / "extension/native-host-contract.json"
    )
    host_path = deploy_native_host(
        source_directory=source_directory,
        labels_path=source_directory.parent / "resources/sidebar-labels.json",
        data_directory=data_home(),
    )

    for browser in installed_browsers():
        enable_accessibility(browser)
        register_native_host(
            native_messaging_directory(browser),
            contract,
            host_path,
        )


if __name__ == "__main__":
    main()
