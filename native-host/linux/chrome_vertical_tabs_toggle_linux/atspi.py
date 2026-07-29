from collections.abc import Iterator
from time import monotonic, sleep
from typing import Literal

import gi

gi.require_version("Atspi", "2.0")
# The version must be selected before importing the GI module.
# fmt: off
from gi.repository import Atspi
# fmt: on

from chrome_vertical_tabs_toggle_linux.iterables import find
from chrome_vertical_tabs_toggle_linux.sidebar_labels import SIDEBAR_LABELS

SidebarState = Literal["collapsed", "expanded"]
SidebarAction = Literal["collapse", "expand"]

SIDEBAR_REGION_CLASS = "VerticalTabStripRegionView"
SIDEBAR_BUTTON_CLASS = "TopContainerButton"
STATE_CHANGE_TIMEOUT_SECONDS = 1.5
COLLAPSE_LABELS = {label.casefold() for label in SIDEBAR_LABELS.collapse}
EXPAND_LABELS = {label.casefold() for label in SIDEBAR_LABELS.expand}


def toggle_active_chrome_sidebar() -> SidebarState:
    window = active_chrome_window()
    button = find_sidebar_toggle(window)
    state = state_after_press(button)
    press(button)
    return wait_for_state(window, state)


def collapse_chrome_sidebars() -> SidebarState:
    windows = tuple(
        window for window in chrome_windows() if find_sidebar_region(window) is not None
    )
    if not windows:
        raise LookupError("Chrome vertical tab strip was not found")

    for window in windows:
        collapse_sidebar(window)
    return "collapsed"


def active_chrome_window() -> Atspi.Accessible:
    active_window = find(
        chrome_windows(),
        lambda window: (
            window.get_state_set().contains(Atspi.StateType.ACTIVE)
            and find_sidebar_region(window) is not None
        ),
    )
    if active_window is not None:
        return active_window
    raise LookupError("active Chrome or Chromium window was not found")


def chrome_windows() -> Iterator[Atspi.Accessible]:
    for application in chrome_applications():
        yield from children(application)


def chrome_applications() -> Iterator[Atspi.Accessible]:
    application_names = {
        "Google Chrome",
        "Google Chrome Beta",
        "Google Chrome Dev",
        "Google Chrome Canary",
        "Chromium",
    }
    desktop = Atspi.get_desktop(0)
    for application in children(desktop):
        if application.get_name() in application_names:
            yield application


def find_sidebar_toggle(window: Atspi.Accessible) -> Atspi.Accessible:
    region = find_sidebar_region(window)
    if region is None:
        raise LookupError("Chrome vertical tab strip was not found")

    button = find(descendants(region), is_sidebar_toggle)
    if button is not None:
        return button
    raise LookupError("Chrome vertical tab toggle was not found")


def find_sidebar_region(window: Atspi.Accessible) -> Atspi.Accessible | None:
    return find(
        descendants(window),
        lambda node: node.get_attributes().get("class") == SIDEBAR_REGION_CLASS,
    )


def is_sidebar_toggle(node: Atspi.Accessible) -> bool:
    if node.get_role_name() != "button":
        return False
    if node.get_attributes().get("class") != SIDEBAR_BUTTON_CLASS:
        return False
    return node.get_name().casefold() in COLLAPSE_LABELS | EXPAND_LABELS


def state_after_press(button: Atspi.Accessible) -> SidebarState:
    if sidebar_action(button) == "collapse":
        return "collapsed"
    return "expanded"


def collapse_sidebar(window: Atspi.Accessible) -> None:
    button = find_sidebar_toggle(window)
    if sidebar_action(button) == "expand":
        return
    press(button)
    wait_for_state(window, "collapsed")


def wait_for_state(
    window: Atspi.Accessible,
    expected_state: SidebarState,
) -> SidebarState:
    deadline = monotonic() + STATE_CHANGE_TIMEOUT_SECONDS
    while monotonic() < deadline:
        button = find_sidebar_toggle(window)
        if current_state(button) == expected_state:
            return expected_state
        sleep(0.05)
    raise TimeoutError("Chrome did not change the vertical tab sidebar state")


def current_state(button: Atspi.Accessible) -> SidebarState:
    if sidebar_action(button) == "expand":
        return "collapsed"
    return "expanded"


def sidebar_action(button: Atspi.Accessible) -> SidebarAction:
    label = button.get_name().casefold()
    if label in COLLAPSE_LABELS:
        return "collapse"
    if label in EXPAND_LABELS:
        return "expand"
    raise ValueError("Chrome vertical tab toggle has an unknown label")


def press(button: Atspi.Accessible) -> None:
    action = button.get_action()
    press_action_index = find(
        range(action.get_n_actions()),
        lambda index: action.get_action_name(index) == "press",
    )
    if press_action_index is None:
        raise LookupError("Chrome vertical tab toggle has no press action")
    if not action.do_action(press_action_index):
        raise RuntimeError("Chrome rejected the sidebar action")


def descendants(root: Atspi.Accessible) -> Iterator[Atspi.Accessible]:
    pending = [root]
    while pending:
        node = pending.pop()
        yield node
        pending.extend(children(node))


def children(node: Atspi.Accessible) -> Iterator[Atspi.Accessible]:
    for index in range(node.get_child_count()):
        child = node.get_child_at_index(index)
        if child is not None:
            yield child
