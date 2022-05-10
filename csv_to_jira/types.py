from typing import TypedDict, Dict, Union, Optional, List

from dataclasses import dataclass


Id = str


class IssueCsvRow(TypedDict, total=False):
    id: str
    summary: str
    size: Optional[float]
    description: Optional[str]
    story: Optional[str]
    notes: Optional[str]
    dependencies: Optional[str]
    __jira_id__: str


@dataclass
class IssueDescriptor:
    id: Id
    summary: str
    size: Optional[float]
    description: str
    labels: List[str]
    issuetype: Optional[str]
    jira_id: Optional[str]


class InstanceDefinition(TypedDict, total=False):
    url: str
    username: str
    password: str
    verify: Union[str, bool]


class ConfigDict(TypedDict, total=False):
    instances: Dict[str, InstanceDefinition]
