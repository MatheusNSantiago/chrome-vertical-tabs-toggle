import json
import shutil
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_CONTRACT_SCHEMA = 2


@dataclass(frozen=True)
class NativeHostContract:
    name: str
    description: str
    extension_id: str


def read_native_host_contract(path: Path) -> NativeHostContract:
    payload = json.loads(path.read_text())
    if payload["schema_version"] != SUPPORTED_CONTRACT_SCHEMA:
        raise ValueError("unsupported native host contract")
    return NativeHostContract(
        name=payload["name"],
        description=payload["description"],
        extension_id=payload["extension_id"],
    )


def deploy_native_host(
    source_directory: Path,
    labels_path: Path,
    data_directory: Path,
) -> Path:
    destination_directory = (
        data_directory / "chrome-vertical-tabs-toggle/native-host/linux"
    )
    resources_directory = destination_directory.parent / "resources"
    destination_package = destination_directory / "chrome_vertical_tabs_toggle_linux"

    destination_directory.mkdir(parents=True, exist_ok=True)
    resources_directory.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_directory / "main.py", destination_directory)
    shutil.copy2(labels_path, resources_directory)
    if destination_package.exists():
        shutil.rmtree(destination_package)
    shutil.copytree(
        source_directory / "chrome_vertical_tabs_toggle_linux",
        destination_package,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    return destination_directory / "main.py"


def register_native_host(
    manifest_directory: Path,
    contract: NativeHostContract,
    host_path: Path,
) -> None:
    manifest_path = manifest_directory / f"{contract.name}.json"
    manifest = {
        "name": contract.name,
        "description": contract.description,
        "path": str(host_path),
        "type": "stdio",
        "allowed_origins": [
            f"chrome-extension://{contract.extension_id}/",
        ],
    }

    manifest_directory.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
