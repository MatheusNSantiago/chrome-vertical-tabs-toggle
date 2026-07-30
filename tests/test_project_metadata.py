import json
import plistlib
import re
import unittest
from pathlib import Path

import tomli

PROJECT_DIRECTORY = Path(__file__).parents[1]
EXTENSION_DIRECTORY = PROJECT_DIRECTORY / "extension"
MESSAGE_REFERENCE = re.compile(r"^__MSG_(.+)__$")


class ProjectMetadataTest(unittest.TestCase):
    def test_versions_match(self) -> None:
        manifest = read_json(EXTENSION_DIRECTORY / "manifest.json")
        pyproject = tomli.loads((PROJECT_DIRECTORY / "pyproject.toml").read_text())
        with (PROJECT_DIRECTORY / "native-host/macos/Info.plist").open("rb") as file:
            macos_bundle = plistlib.load(file)

        self.assertEqual(manifest["version"], pyproject["project"]["version"])
        self.assertEqual(
            manifest["version"],
            macos_bundle["CFBundleShortVersionString"],
        )
        self.assertEqual(manifest["version"], macos_bundle["CFBundleVersion"])

    def test_manifest_messages_exist_in_default_locale(self) -> None:
        manifest = read_json(EXTENSION_DIRECTORY / "manifest.json")
        messages = read_json(
            EXTENSION_DIRECTORY
            / "_locales"
            / manifest["default_locale"]
            / "messages.json"
        )
        localized_values = (
            manifest["name"],
            manifest["description"],
            manifest["action"]["default_title"],
            manifest["commands"]["toggle-vertical-tabs"]["description"],
        )

        for value in localized_values:
            match = MESSAGE_REFERENCE.fullmatch(value)
            self.assertIsNotNone(match)
            self.assertIn(match.group(1), messages)

    def test_manifest_icons_exist(self) -> None:
        manifest = read_json(EXTENSION_DIRECTORY / "manifest.json")
        icon_paths = (
            *manifest["icons"].values(),
            *manifest["action"]["default_icon"].values(),
        )

        for icon_path in icon_paths:
            self.assertTrue((EXTENSION_DIRECTORY / icon_path).is_file())


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


if __name__ == "__main__":
    unittest.main()
