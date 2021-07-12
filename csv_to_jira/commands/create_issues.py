import argparse
import csv

from jira.resources import Issue
from pathlib import Path
from rich.prompt import Confirm
from typing import Tuple, Dict, Optional, List

from ..exceptions import UserError
from ..types import IssueDescriptor
from ..constants import JIRA_ID_FIELD
from ..plugin import BaseCommand, BaseReader, get_installed_readers


class InvalidIssueType(UserError):
    pass


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return """Generate a digraph showing calculated issue dependencies."""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        available_readers = get_installed_readers()

        parser.add_argument(
            "path",
            type=Path,
        )
        parser.add_argument(
            "project", type=str, help="Jira project within which to create new issues."
        )
        parser.add_argument(
            "--reader", type=str, choices=available_readers, default="default"
        )
        parser.add_argument("--issuetype", type=str, default="Story")
        parser.add_argument("--relationship", type=str, default="Blocks")

    def handle(self):
        available_readers = get_installed_readers()
        issue_reader: BaseReader = available_readers[self.options.reader](
            self.config, self.options
        )

        issues: Dict[str, Tuple[IssueDescriptor, Issue]] = {}
        csv_records: List[Dict] = []
        with open(self.options.path, "r") as inf:
            reader = csv.DictReader(inf)
            for row in reader:
                csv_records.append(row)

        with open(self.options.path, "w") as outf:
            final_fieldnames = reader.fieldnames
            if JIRA_ID_FIELD not in final_fieldnames:
                final_fieldnames.append(JIRA_ID_FIELD)

            writer = csv.DictWriter(outf, fieldnames=final_fieldnames)
            writer.writeheader()

            for row in csv_records:
                record = issue_reader.process_row(row)

                jira_issue: Optional[Issue] = None
                if record.jira_id:
                    jira_issue = self.jira.issue(record.jira_id)
                elif Confirm.ask(
                    f'Create issue for [u]"{record.summary}" ({record.id})[/u]?'
                ):
                    jira_issue = self.jira.create_issue(
                        fields={
                            "project": self.options.project,
                            "summary": record.summary,
                            "description": record.description,
                            "issuetype": {
                                "name": self.options.issuetype,
                            },
                        }
                    )

                issues[record.id] = (record, jira_issue)

                row[JIRA_ID_FIELD] = jira_issue.key if jira_issue else ""
                writer.writerow(row)
                outf.flush()

        all_records = [x for (x, _) in issues.values()]
        for record, issue in issues.values():
            dependencies = issue_reader.get_dependencies(record, all_records)
            for dep in dependencies:
                jira_dep = issues[dep.id][1]
                if not jira_dep:
                    continue

                found_link = False
                for link in jira_dep.fields.issuelinks:
                    if (
                        link.type.name == self.options.relationship
                        and link.outwardIssue.key == issue.key
                    ):
                        found_link = True

                if not found_link:
                    if Confirm.ask(
                        "Create relationship"
                        f' [u]"{jira_dep.fields.summary}" ({dep.id})[/u]'
                        f" [b]{self.options.relationship}[/b]"
                        f' [u]"{issue.fields.summary}" ({record.id})[/u]?'
                    ):
                        self.jira.create_issue_link(
                            type=self.options.relationship,
                            inwardIssue=jira_dep.key,
                            outwardIssue=issue.key,
                        )
