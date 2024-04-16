import IPython

from ..plugin import BaseCommand


class Command(BaseCommand):
    @classmethod
    def get_help(cls) -> str:
        return """Open a shell from which you can access Jira"""

    def handle(self):
        IPython.embed(evaluation="dangerous")
