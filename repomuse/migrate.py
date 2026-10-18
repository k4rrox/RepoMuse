"""Upgrade an Open Source Radar v1 `daily.json` to the RepoMuse v2 editions file."""
from .schema import SCHEMA_VERSION, require, validate_data


def upgrade(data):
    require(isinstance(data, dict), "input must be a JSON object")
    if data.get("schema_version") == SCHEMA_VERSION:
        return validate_data(data), None
    require(data.get("schema_version") == 1, "only schema_version 1 files can be upgraded")
    upgraded = {"schema_version": SCHEMA_VERSION, "sample": bool(data.get("demo")), "editions": data.get("editions")}
    return validate_data(upgraded), data.get("timezone")
