from datetime import datetime

import click

from .base_cli_view import BaseClickCommand


@click.command(cls=BaseClickCommand, name="health")
def health_cli_view() -> None:
    now = datetime.now().astimezone().isoformat()
    print(now)
