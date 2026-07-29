import json
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_LABELS_SCHEMA = 1


@dataclass(frozen=True)
class SidebarLabels:
    collapse: frozenset[str]
    expand: frozenset[str]


def read_sidebar_labels(path: Path) -> SidebarLabels:
    payload = json.loads(path.read_text())
    if payload["schema_version"] != SUPPORTED_LABELS_SCHEMA:
        raise ValueError("unsupported sidebar labels")
    return SidebarLabels(
        collapse=frozenset(payload["collapse"]),
        expand=frozenset(payload["expand"]),
    )


SIDEBAR_LABELS = read_sidebar_labels(
    Path(__file__).parents[2] / "resources/sidebar-labels.json"
)
