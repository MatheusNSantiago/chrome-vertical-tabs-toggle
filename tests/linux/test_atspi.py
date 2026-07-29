import unittest
from importlib.util import find_spec

GI_AVAILABLE = find_spec("gi") is not None
if GI_AVAILABLE:
    from chrome_vertical_tabs_toggle_linux.atspi import (
        find_sidebar_toggle,
        is_sidebar_toggle,
    )


class AccessibleNode:
    def __init__(
        self,
        role: str,
        name: str = "",
        class_name: str = "",
        children: tuple["AccessibleNode", ...] = (),
    ) -> None:
        self.role = role
        self.name = name
        self.class_name = class_name
        self.children = children

    def get_role_name(self) -> str:
        return self.role

    def get_name(self) -> str:
        return self.name

    def get_attributes(self) -> dict[str, str]:
        return {"class": self.class_name}

    def get_child_count(self) -> int:
        return len(self.children)

    def get_child_at_index(self, index: int) -> "AccessibleNode":
        return self.children[index]


@unittest.skipUnless(GI_AVAILABLE, "AT-SPI belongs to the system Python")
class SidebarDiscoveryTest(unittest.TestCase):
    def test_ignores_a_page_button_with_the_same_accessible_name(self) -> None:
        page_button = AccessibleNode("button", "Expand tabs")
        sidebar_button = AccessibleNode(
            "button",
            "Expand tabs",
            "TopContainerButton",
        )
        sidebar = AccessibleNode(
            "page tab list",
            class_name="VerticalTabStripRegionView",
            children=(sidebar_button,),
        )
        window = AccessibleNode("frame", children=(page_button, sidebar))

        self.assertIs(find_sidebar_toggle(window), sidebar_button)

    def test_requires_the_native_sidebar_button_class(self) -> None:
        page_button = AccessibleNode("button", "Expand tabs")

        self.assertFalse(is_sidebar_toggle(page_button))


if __name__ == "__main__":
    unittest.main()
