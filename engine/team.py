"""Team config loader — roster, briefs, phases, limits from team.yaml."""

from functools import lru_cache
from pathlib import Path

import yaml

TEAM_FILE = Path(__file__).resolve().parent / "team.yaml"


@lru_cache(maxsize=1)
def load_team() -> dict:
    return yaml.safe_load(TEAM_FILE.read_text(encoding="utf-8"))


def role(key: str) -> dict:
    return load_team()["roles"][key]


def role_label(key: str) -> str:
    return load_team()["roles"].get(key, {}).get("label", key)


def role_color(key: str) -> str:
    return load_team()["roles"].get(key, {}).get("color", "#9AA4B2")


def phases() -> list[dict]:
    return load_team()["phases"]


def limits() -> dict:
    return load_team()["limits"]
