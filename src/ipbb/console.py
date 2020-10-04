from rich.console import Console

console = Console()

def cprint(*args, **kwargs):
    console.print(*args, **kwargs)