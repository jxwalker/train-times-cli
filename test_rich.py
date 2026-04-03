from rich.console import Console
from rich.table import Table

console = Console(width=40, force_terminal=False)
table = Table(title="Live Departures: HPD -> CTK")
table.add_column("Time", style="cyan")
table.add_column("Dest", style="magenta")
table.add_column("Plat", style="green")

table.add_row("17:52", "Brighton", "1")
table.add_row("17:55", "Rainham", "1")
table.add_row("18:08", "ThreBdg", "1")
console.print(table)
