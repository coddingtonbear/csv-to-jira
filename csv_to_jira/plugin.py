from __future__ import annotations

from abc import ABCMeta, abstractmethod
import argparse
import logging
from typing import (
    Dict,
    Iterable,
    Optional,
    Type,
    cast,
)

import pkg_resources

import keyring
from jira import JIRA
from rich.console import Console
from urllib3 import disable_warnings

from .constants import APP_NAME
from .exceptions import ConfigurationError
from .types import ConfigDict, InstanceDefinition, IssueDescriptor
from . import config


logger = logging.getLogger(__name__)


def get_installed_commands() -> Dict[str, Type[BaseCommand]]:
    possible_commands: Dict[str, Type[BaseCommand]] = {}
    for entry_point in pkg_resources.iter_entry_points(group="csv_to_jira.commands"):
        try:
            loaded_class = entry_point.load()
        except ImportError:
            logger.warning(
                "Attempted to load entrypoint %s, but " "an ImportError occurred.",
                entry_point,
            )
            continue
        if not issubclass(loaded_class, BaseCommand):
            logger.warning(
                "Loaded entrypoint %s, but loaded class is "
                "not a subclass of `csv_to_jira.plugin.BaseCommand`.",
                entry_point,
            )
            continue
        possible_commands[entry_point.name] = loaded_class

    return possible_commands


class BaseCommand(metaclass=ABCMeta):
    _jira: Optional[JIRA] = None

    def __init__(self, config: ConfigDict, options: argparse.Namespace):
        self._config: ConfigDict = config
        self._options: argparse.Namespace = options
        self._console = Console(highlight=False)
        super().__init__()

    @property
    def config(self) -> ConfigDict:
        """ Provides the configuration dictionary."""
        return self._config

    def save_config(self) -> None:
        """ Saves the existing configuration dictionary."""
        config.save(self.config, self.options.config)

    @property
    def options(self) -> argparse.Namespace:
        """ Provides options provided at the command-line."""
        return self._options

    @property
    def console(self) -> Console:
        """ Provides access to the console (see `rich.console.Console`."""
        return self._console

    @property
    def jira(self) -> JIRA:
        """ Provides access to the configured Jira instance."""
        if self._jira is None:
            instance: Dict[InstanceDefinition] = cast(  # type: ignore
                InstanceDefinition,
                self.config.get("instances", {}).get(self.options.instance_name, {}),
            )

            instance_url = self.options.instance_url or instance.get("url")
            if not instance_url:
                raise ConfigurationError(
                    "instance_url not set; please run `jira-select configure`."
                )

            username = self.options.username or instance.get("username")
            if not username:
                raise ConfigurationError(
                    "username not set; please run `jira-select configure`."
                )

            password = self.options.password or instance.get("password")
            if not password:
                password = keyring.get_password(APP_NAME, instance_url + username)
                if not password:
                    raise ConfigurationError(
                        f"Password not stored for {instance_url} user {username}; "
                        "use the 'store-password' command to store the password "
                        "for this user account in your system keyring or use "
                        "`jira-select configure`."
                    )

            verify = self.options.disable_certificate_verification or instance.get(
                "verify"
            )
            if verify is None:
                verify = True
            if verify is False:
                disable_warnings()

            self._jira = JIRA(
                options={
                    "agile_rest_path": "agile",
                    "server": instance_url,
                    "verify": verify,
                },
                basic_auth=(username, password),
            )

        return self._jira

    @classmethod
    def get_help(cls) -> str:
        """ Retuurns help text for this function."""
        return ""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        """ Allows adding additional command-line arguments. """
        pass

    @abstractmethod
    def handle(self) -> None:
        """ This is where the work of your function starts. """
        ...


def get_installed_readers() -> Dict[str, Type[BaseReader]]:
    possible_readers: Dict[str, Type[BaseReader]] = {}
    for entry_point in pkg_resources.iter_entry_points(group="csv_to_jira.readers"):
        try:
            loaded_class = entry_point.load()
        except ImportError:
            logger.warning(
                "Attempted to load entrypoint %s, but " "an ImportError occurred.",
                entry_point,
            )
            continue
        if not issubclass(loaded_class, BaseReader):
            logger.warning(
                "Loaded entrypoint %s, but loaded class is "
                "not a subclass of `csv_to_jira.plugin.BaseReader`.",
                entry_point,
            )
            continue
        possible_readers[entry_point.name] = loaded_class

    return possible_readers


class BaseReader(metaclass=ABCMeta):
    def __init__(self, config: ConfigDict, options: argparse.Namespace):
        self._config: ConfigDict = config
        self._options: argparse.Namespace = options
        super().__init__()

    @property
    def config(self) -> ConfigDict:
        """ Provides the configuration dictionary."""
        return self._config

    @property
    def options(self) -> argparse.Namespace:
        """ Provides options provided at the command-line."""
        return self._options

    @abstractmethod
    def process_row(self, row: Dict) -> IssueDescriptor:
        ...

    def get_dependencies(self, row: IssueDescriptor, rows: Iterable[IssueDescriptor]) -> Iterable[IssueDescriptor]:
        return []
