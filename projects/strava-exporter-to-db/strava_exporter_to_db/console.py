import sys

from rich.console import Console


class ConsoleAdapter:
    def __init__(self):
        self.stdout_console = Console(file=sys.stdout)
        self.stderr_console = Console(file=sys.stderr)

    def log(self, *args, **kwargs):
        # if not settings.IS_TEST:
        # Use _stack_offset=2 to get to the original source line that
        #  invoked the log statement.
        kwargs["_stack_offset"] = 2
        return self.stderr_console.log(*args, **kwargs)

    def print(self, *args, **kwargs):
        # if not settings.IS_TEST:
        return self.stdout_console.print(*args, **kwargs)

    def input(self, *args, **kwargs):
        return self.stdout_console.input(*args, **kwargs)


console = ConsoleAdapter()
