from typing import TypedDict, Dict, Union, Optional

from dataclasses import dataclass


Id = str


@dataclass
class IssueDescriptor:
    id: Id
    summary: str
    size: Optional[float]
    description: str
    jira_id: Optional[str]


class InstanceDefinition(TypedDict, total=False):
    url: str
    username: str
    password: str
    verify: Union[str, bool]


class ConfigDict(TypedDict, total=False):
    instances: Dict[str, InstanceDefinition]
