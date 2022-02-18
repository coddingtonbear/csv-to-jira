from dataclasses import dataclass
from typing import List, Dict, Iterable

from ..plugin import BaseReader
from ..types import IssueDescriptor
from ..constants import JIRA_ID_FIELD


@dataclass
class AgileIssueDescriptor(IssueDescriptor):
    dependency_ids: List[str]


class Reader(BaseReader):
    def process_row(self, row: Dict) -> AgileIssueDescriptor:
        return AgileIssueDescriptor(
            id=row["id"],
            summary=row["summary"],
            size=float(row["size"]),
            description="\n\n---\n\n".join([row["story"], row["notes"]]),
            jira_id=row.get(JIRA_ID_FIELD),
            dependency_ids=row["dependencies"].split(","),
        )

    def get_dependencies(self, row: AgileIssueDescriptor, rows: Iterable[AgileIssueDescriptor]) -> Iterable[AgileIssueDescriptor]:  # type: ignore[override]
        return filter(lambda dep_row: dep_row.id in row.dependency_ids, rows)
