import argparse
import csv
import os
import shutil

from jira.resources import Issue
from pathlib import Path
from rich.prompt import Confirm
from typing import cast, Tuple, Dict, List, Any

from ..exceptions import UserError, Abort
from ..types import IssueDescriptor
from ..constants import JIRA_ID_FIELD
from ..plugin import BaseCommand, BaseReader, get_installed_readers


class InvalidIssueType(UserError):
    pass


def field_and_value(arg: str) -> Tuple[str, str]:
    return cast(Tuple[str, str], tuple(arg.split("=", 1)))


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
        parser.add_argument("--setfield", type=field_and_value, nargs="*", default=[])
        parser.add_argument("--label", type=str, nargs="*", default=[])
        parser.add_argument(
            "--no-issues",
            default=True,
            dest="update_or_create_issues",
            action="store_false",
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

        temporary_path = Path(os.path.dirname(self.options.path)) / Path(
            os.path.basename(self.options.path) + ".tmp"
        )
        skip_all = False
        with open(temporary_path, "w") as outf:
            final_fieldnames = reader.fieldnames
            if JIRA_ID_FIELD not in final_fieldnames:
                final_fieldnames.append(JIRA_ID_FIELD)

            writer = csv.DictWriter(outf, fieldnames=final_fieldnames)
            writer.writeheader()

            for row in csv_records:
                record = issue_reader.process_row(row)

                fields: Dict[str, Any] = {
                    "project": self.options.project,
                    "summary": record.summary,
                    "description": record.description,
                    "labels": self.options.label + record.labels,
                }
                if record.issuetype:
                    fields["issuetype"] = record.issuetype
                elif self.options.issuetype:
                    fields["issuetype"] = {"name": self.options.issuetype}
                if record.size:
                    fields["customfield_10069"] = record.size

                for field, value in self.options.setfield:
                    fields[field] = value

                try:
                    if not skip_all:
                        if not record.jira_id:
                            if self.options.update_or_create_issues:
                                if Confirm.ask(
                                    f'Create issue for [u]"{record.summary}" ({record.id})[/u]?'
                                ):
                                    jira_issue = self.jira.create_issue(fields=fields)
                                else:
                                    raise Abort(f"Issue for {record.id} does not exist")
                        else:
                            jira_issue = self.jira.issue(record.jira_id)
                            if self.options.update_or_create_issues and Confirm.ask(
                                f'Update issue for [u]"{record.summary}" ({record.id})[/u]?'
                            ):
                                jira_issue.update(fields)
                except (KeyboardInterrupt, Abort):
                    skip_all = True

                issues[record.id] = (record, jira_issue)

                row[JIRA_ID_FIELD] = jira_issue.key if jira_issue else ""
                writer.writerow(row)
                outf.flush()

        shutil.move(temporary_path, self.options.path)

        for record, issue in issues.values():
            dependencies = issue_reader.get_dependencies(self.jira, record, issues)
            for jira_dep in dependencies:
                found_link = False
                for link in jira_dep.fields.issuelinks:
                    # If there's no 'outwardIssue' field, we're looking
                    # at the relationship from the other side; so we
                    # can just skip these.
                    if not hasattr(link, "outwardIssue"):
                        continue

                    if (
                        link.type.name == self.options.relationship
                        and link.outwardIssue.key == issue.key
                    ):
                        found_link = True

                if not found_link:
                    if Confirm.ask(
                        "Create relationship"
                        f' [u]"{jira_dep.fields.summary}" ({jira_dep.key})[/u]'
                        f" [b]{self.options.relationship}[/b]"
                        f' [u]"{issue.fields.summary}" ({record.id})[/u]?'
                    ):
                        self.jira.create_issue_link(
                            type=self.options.relationship,
                            inwardIssue=jira_dep.key,
                            outwardIssue=issue.key,
                        )
