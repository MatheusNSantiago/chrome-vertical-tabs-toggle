import json
from io import BytesIO
from pathlib import Path
from tarfile import open as open_tar
from typing import TypedDict
from urllib.request import urlopen
from xml.etree import ElementTree as ET

RESOURCE_DIRECTORY = "chrome/app/resources"
SIDEBAR_RESOURCE_IDS = {
    "collapse": {"2729310339366257582", "5204584298075822291"},
    "expand": {"1386966479075994683", "7194343495483122559"},
}
FALLBACK_LABELS = {
    "collapse": {"Collapse tabs"},
    "expand": {"Expand tabs"},
}


class LabelsSource(TypedDict):
    chromium_revision: str
    resource_ids: dict[str, list[str]]
    locale_resource_count: int


class GeneratedLabels(TypedDict):
    schema_version: int
    source: LabelsSource
    collapse: list[str]
    expand: list[str]


def chromium_revision() -> str:
    payload = fetch(
        "https://chromium.googlesource.com/chromium/src/+log/main?format=JSON"
    )
    return json.loads(payload.removeprefix(b")]}'\n"))["log"][0]["commit"]


def gitiles_url(revision: str, path: str, suffix: str) -> str:
    return f"https://chromium.googlesource.com/chromium/src/+/{revision}/{path}{suffix}"


def fetch(url: str) -> bytes:
    with urlopen(url) as response:
        return response.read()


def locale_resources(revision: str) -> list[str]:
    payload = fetch(gitiles_url(revision, RESOURCE_DIRECTORY + "/", "?format=JSON"))
    listing = json.loads(payload.removeprefix(b")]}'\n"))
    return [
        entry["name"]
        for entry in listing["entries"]
        if entry["name"].startswith("generated_resources_")
        and entry["name"].endswith(".xtb")
    ]


def translation_documents(revision: str, resources: list[str]) -> list[bytes]:
    archive_url = (
        "https://chromium.googlesource.com/chromium/src/"
        f"+archive/{revision}/{RESOURCE_DIRECTORY}.tar.gz"
    )
    with open_tar(fileobj=BytesIO(fetch(archive_url)), mode="r:gz") as archive:
        return [archive.extractfile(resource).read() for resource in resources]


def labels_from_translation_documents(documents: list[bytes]) -> dict[str, list[str]]:
    translated_labels = {state: set() for state in FALLBACK_LABELS}
    resource_states = {
        resource_id: state
        for state, resource_ids in SIDEBAR_RESOURCE_IDS.items()
        for resource_id in resource_ids
    }
    translations = (
        translation
        for document in documents
        for translation in ET.fromstring(document).findall("translation")
    )

    for translation in translations:
        state = resource_states.get(translation.attrib["id"])
        if state is None:
            continue
        translated_labels[state].add("".join(translation.itertext()).strip())

    missing_states = [
        state for state, values in translated_labels.items() if not values
    ]
    if missing_states:
        raise ValueError(
            "Chromium sidebar translations were not found for: "
            + ", ".join(missing_states)
        )

    return {
        state: sorted(values | FALLBACK_LABELS[state])
        for state, values in translated_labels.items()
    }


def generate_labels() -> GeneratedLabels:
    revision = chromium_revision()
    resources = locale_resources(revision)
    if not resources:
        raise ValueError("Chromium locale resources were not found")
    labels = labels_from_translation_documents(
        translation_documents(revision, resources)
    )
    return {
        "schema_version": 1,
        "source": {
            "chromium_revision": revision,
            "resource_ids": {
                state: sorted(ids) for state, ids in SIDEBAR_RESOURCE_IDS.items()
            },
            "locale_resource_count": len(resources),
        },
        "collapse": labels["collapse"],
        "expand": labels["expand"],
    }


def main() -> None:
    labels_path = (
        Path(__file__).parent.parent / "native-host/resources/sidebar-labels.json"
    )
    labels = generate_labels()
    labels_path.write_text(json.dumps(labels, ensure_ascii=False, indent=2) + "\n")
    print(
        f"Updated sidebar labels from Chromium {labels['source']['chromium_revision']}"
    )


if __name__ == "__main__":
    main()
