#!/usr/bin/python3

import sys

from chrome_vertical_tabs_toggle_linux.atspi import (
    SidebarState,
    collapse_chrome_sidebars,
    toggle_active_chrome_sidebar,
)
from chrome_vertical_tabs_toggle_linux.native_messaging import (
    TOGGLE_COMMAND,
    NativeCommand,
    read_command,
    write_response,
)


def control_chrome_sidebars(command: NativeCommand) -> SidebarState:
    if command == TOGGLE_COMMAND:
        return toggle_active_chrome_sidebar()
    return collapse_chrome_sidebars()


def main() -> None:
    try:
        command = read_command(sys.stdin.buffer)
        state = control_chrome_sidebars(command)
    except Exception as error:  # noqa: BLE001
        write_response(sys.stdout.buffer, {"error": str(error)})
        return
    write_response(sys.stdout.buffer, {"state": state})


if __name__ == "__main__":
    main()
