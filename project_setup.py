from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "run_mode": "fast",
    "inputs": {
        "allow_network": False,
        "use_existing_data": True,
    },
    "outputs": {
        "overwrite_data": False,
        "overwrite_artifacts": False,
    },
    "openalex": {
        "sample_limit": None,
        "sample_include_work_ids": [],
    },
    "external_validation": {
        "sample_limit": None,
        "max_dois_per_researcher": None,
    },
}


@dataclass(frozen=True)
class ProjectSetup:
    project_folder: Path
    config_path: Path
    project_config: dict[str, Any]
    run_mode: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    openalex: dict[str, Any]
    allow_network: bool
    use_existing_data: bool
    overwrite_data: bool
    overwrite_artifacts: bool
    openalex_sample_limit: int | None
    openalex_sample_include_work_ids: list[str]


def find_project_root(start: Path | str | None = None) -> Path:
    start_path = Path.cwd().resolve() if start is None else Path(start).resolve()

    for candidate in [start_path, *start_path.parents]:
        if (candidate / "config" / "project_config.yaml").exists():
            return candidate

        child_matches = sorted(
            child
            for child in candidate.iterdir()
            if child.is_dir() and (child / "config" / "project_config.yaml").exists()
        )
        if len(child_matches) == 1:
            return child_matches[0]

    raise FileNotFoundError(
        "Could not find config/project_config.yaml. Run from the project folder."
    )


def parse_config_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_config_scalar(item.strip()) for item in inner.split(",")]

    lower = value.lower()
    if lower in {"true", "yes"}:
        return True
    if lower in {"false", "no"}:
        return False
    if lower in {"none", "null", "~"}:
        return None

    try:
        return int(value)
    except ValueError:
        return value.strip('"').strip("'")


def load_simple_yaml_config(config_path: Path) -> dict[str, Any]:
    loaded_config: dict[str, Any] = {}
    current_section: str | None = None

    for raw_line in config_path.read_text().splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip())
        text = raw_line.strip()

        if ":" not in text:
            continue

        key, value = text.split(":", 1)
        key = key.strip()
        value = parse_config_scalar(value)

        if indent == 0:
            if value is None:
                loaded_config[key] = {}
                current_section = key
            else:
                loaded_config[key] = value
                current_section = key if isinstance(value, dict) else None
        elif current_section is not None:
            loaded_config.setdefault(current_section, {})[key] = value

    return loaded_config


def merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = {
        key: value.copy() if isinstance(value, dict) else value
        for key, value in base.items()
    }

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value

    return merged


def load_project_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return merge_config(DEFAULT_CONFIG, {})

    try:
        import yaml

        loaded_config = yaml.safe_load(config_path.read_text()) or {}
    except ImportError:
        loaded_config = load_simple_yaml_config(config_path)

    return merge_config(DEFAULT_CONFIG, loaded_config)


def normalize_work_id_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def setup_project(start: Path | str | None = None) -> ProjectSetup:
    project_folder = find_project_root(start)
    if str(project_folder) not in sys.path:
        sys.path.insert(0, str(project_folder))

    config_path = project_folder / "config" / "project_config.yaml"
    project_config = load_project_config(config_path)

    inputs = project_config.get("inputs", {})
    outputs = project_config.get("outputs", {})
    openalex = project_config.get("openalex", {})

    return ProjectSetup(
        project_folder=project_folder,
        config_path=config_path,
        project_config=project_config,
        run_mode=project_config.get("run_mode", "fast"),
        inputs=inputs,
        outputs=outputs,
        openalex=openalex,
        allow_network=bool(inputs.get("allow_network", False)),
        use_existing_data=bool(inputs.get("use_existing_data", True)),
        overwrite_data=bool(outputs.get("overwrite_data", False)),
        overwrite_artifacts=bool(outputs.get("overwrite_artifacts", False)),
        openalex_sample_limit=openalex.get("sample_limit"),
        openalex_sample_include_work_ids=normalize_work_id_list(
            openalex.get("sample_include_work_ids")
        ),
    )


def ensure_dirs(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def load_env_file(path: Path) -> bool:
    if not path.exists():
        return False

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

    return True


def load_project_env(project_folder: Path) -> list[str]:
    return [
        str(path.relative_to(project_folder))
        for path in [project_folder / ".env", project_folder / "key.env"]
        if load_env_file(path)
    ]
