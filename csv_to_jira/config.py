import os
from pathlib import Path

from appdirs import user_config_dir
from yaml import safe_dump, safe_load

from .constants import APP_NAME
from .types import ConfigDict


def get_dir() -> Path:
    root_path = Path(user_config_dir(APP_NAME, "coddingtonbear"))
    os.makedirs(root_path, exist_ok=True)

    return root_path


def get_default_path() -> Path:
    root_path = get_dir()
    return Path(os.path.join(root_path, "config.yaml"))


def get(path: Path = None) -> ConfigDict:
    if path is None:
        path = get_default_path()

    if not os.path.isfile(path):
        return {}

    with open(path, "r") as inf:
        return safe_load(inf)


def save(data: ConfigDict, path: Path = None) -> None:
    if path is None:
        path = get_default_path()

    with open(path, "w") as outf:
        safe_dump(data, outf)
