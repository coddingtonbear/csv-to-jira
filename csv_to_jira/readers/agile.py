from dataclasses import dataclass
import logging
from typing import cast, Dict, List, Iterable, Optional, Tuple

from jira import JIRA, Issue

from ..plugin import BaseReader
from ..types import IssueCsvRow, IssueDescriptor
from ..constants import JIRA_ID_FIELD


logger = logging.getLogger(__name__)


@dataclass
class AgileIssueDescriptor(IssueDescriptor):
    dependency_ids: List[str]


class Reader(BaseReader):
    def process_row(self, row: IssueCsvRow) -> AgileIssueDescriptor:  # type: ignore
        description_fields: List[str] = []
        for field in ['description', 'story', 'notes']:
            if row.get(field):
                description_fields.append(row[field])  # type: ignore

        size: Optional[float] = None
        _size = row.get('size')
        if _size:
            size = float(_size)

        return AgileIssueDescriptor(
            id=row["id"],
            summary=row["summary"],
            size=size,
            description="\n\n---\n\n".join(description_fields),
            jira_id=cast(Optional[str], row.get(JIRA_ID_FIELD)),
            dependency_ids=[x for x in (row.get("dependencies") or "").split(",") if x],
        )

    def get_dependency_names(self, row: AgileIssueDescriptor) -> Iterable[str]:  # type: ignore[override]
        return row.dependency_ids

    def get_dependencies(self, jira: JIRA, row: AgileIssueDescriptor, rows: Dict[str, Tuple[IssueDescriptor, Issue]]) -> Iterable[Issue]:  # type: ignore[override]
        for dep_name in row.dependency_ids:
            try:
                if '-' in dep_name:
                    yield jira.issue(dep_name)
                else:
                    yield rows[dep_name][1]
            except Exception:
                logger.exception("Could not find dependency matching '%s'", dep_name)
