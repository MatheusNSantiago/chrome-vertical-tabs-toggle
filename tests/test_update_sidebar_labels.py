import unittest
from unittest.mock import patch

from update_sidebar_labels import (
    generate_labels,
    labels_from_translation_documents,
)


class SidebarLabelsTest(unittest.TestCase):
    def test_extracts_each_sidebar_state_from_translated_resources(self) -> None:
        document = b"""<?xml version="1.0"?>
        <translationbundle>
          <translation id="1386966479075994683">Mostrar guias</translation>
          <translation id="2729310339366257582">Ocultar guias</translation>
        </translationbundle>"""

        labels = labels_from_translation_documents([document])

        self.assertIn("Mostrar guias", labels["expand"])
        self.assertIn("Ocultar guias", labels["collapse"])
        self.assertIn("Expand tabs", labels["expand"])
        self.assertIn("Collapse tabs", labels["collapse"])

    def test_generated_schema_is_versioned(self) -> None:
        document = b"""<translationbundle>
          <translation id="1386966479075994683">Expand tabs</translation>
          <translation id="2729310339366257582">Collapse tabs</translation>
        </translationbundle>"""
        with (
            patch(
                "update_sidebar_labels.chromium_revision",
                return_value="revision",
            ),
            patch(
                "update_sidebar_labels.locale_resources",
                return_value=["generated_resources_en-GB.xtb"],
            ),
            patch(
                "update_sidebar_labels.translation_documents",
                return_value=[document],
            ),
        ):
            labels = generate_labels()

        self.assertEqual(labels["schema_version"], 1)

    def test_rejects_a_chromium_revision_without_sidebar_translations(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Chromium sidebar translations were not found",
        ):
            labels_from_translation_documents([b"<translationbundle />"])
