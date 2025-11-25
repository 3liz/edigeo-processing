
from importlib import resources
from pathlib import Path
from typing import (
    cast,
)

PACKAGE_NAME = "qgis_edigeo_processing"

def plugin_path(*args: str | Path) -> Path:
    return cast("Path", resources.files(PACKAGE_NAME)).joinpath(*args)


def resources_path(*args) -> Path:
    return plugin_path("resources", *args)
