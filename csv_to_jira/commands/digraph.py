import argparse
import csv
from csv_to_jira.types import IssueDescriptor
from pathlib import Path
import textwrap
from typing import List

from ..plugin import BaseCommand, BaseReader, get_installed_readers


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
            "out_path",
            type=Path,
        )
        parser.add_argument(
            "--reader", type=str, choices=available_readers, default="default"
        )

    def handle(self):
        available_readers = get_installed_readers()
        issue_reader: BaseReader = available_readers[self.options.reader](
            self.config, self.options
        )

        with open(self.options.path, "r") as inf:
            reader = csv.DictReader(inf)

            issues: List[IssueDescriptor] = []
            for row in reader:
                record = issue_reader.process_row(row)
                issues.append(record)

        with open(self.options.out_path, "w") as outf:
            lines = ["digraph issues {"]

            for issue in issues:
                wrapped = "<BR/>".join(textwrap.wrap(issue.summary, 20))
                lines.append(f"\tid{issue.id}[shape=box,label=<<B>{issue.id}</B><BR/>{wrapped}<BR/>{issue.size} pts>,height={issue.size * 1.25}]")

            for issue in issues:
                dep_names = issue_reader.get_dependency_names(issue)
                for dep in dep_names:
                    dep_name: str = f"id{dep}"
                    if '-' in dep:
                        dep_name = f"\"{dep}\""

                    lines.append(f"\t{dep_name} -> id{issue.id} [arrowhead=normal]")

            lines.append("}")

            outf.write("\n".join(lines))
