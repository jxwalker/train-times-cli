import sys
from rich.console import Console
from rich.table import Table
from rich import box

console = Console(width=32, force_terminal=False)
table = Table(title="Live: HPD -> CTK", box=box.SIMPLE)
table.add_column("Time")
table.add_column("Dest")
table.add_column("Plat")
table.add_row("17:52", "Brighton"[:10], "1")
table.add_row("17:55", "Rainham (Kent)"[:10], "1")
console.print(table)
