import typer
import requests
import json
from datetime import datetime, timedelta
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import box
import re
import sys
import contextlib

app = typer.Typer(help="UK Train Times and London Underground CLI")

is_piped = not sys.stdout.isatty()
if is_piped:
    console = Console(width=32, force_terminal=False)
else:
    console = Console()

@contextlib.contextmanager
def get_status(msg: str):
    if is_piped:
        yield
    else:
        with console.status(msg):
            yield

def format_time(ts: str) -> str:
    """Helper to format API times nicely."""
    if not ts:
        return "-"
    return ts

@app.command()
def tube():
    """
    Check for any problems on the London Underground network.
    """
    url = "https://api.tfl.gov.uk/Line/Mode/tube/Status"
    with get_status("[bold blue]Checking London Underground status..."):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            console.print(f"[bold red]Failed to fetch Tube status: {e}[/bold red]")
            raise typer.Exit(1)
            
    table = Table(title="London Underground Status")
    table.add_column("Line", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Reason", style="green")

    problems_found = False
    for line in data:
        name = line.get("name", "Unknown")
        statuses = line.get("lineStatuses", [])
        if not statuses:
            continue
            
        status = statuses[0]
        severity = status.get("statusSeverityDescription", "Unknown")
        reason = status.get("reason", "")
        
        if severity != "Good Service":
            problems_found = True
            table.add_row(name, severity, reason)
            
    if not problems_found:
        console.print("[bold green]✅ Good Service on all London Underground lines![/bold green]")
    else:
        console.print(table)


@app.command()
def live(
    start: str = typer.Argument(..., help="Start station CRS code (e.g. VIC)"),
    dest: str = typer.Argument(None, help="Optional destination CRS code (e.g. BTN)"),
    allow: int = typer.Option(0, "--allow", "-a", help="Travel buffer: allow X minutes travel to station, don't show trains before this.")
):
    """
    Fetch the live departure board for a station.
    """
    start = start.upper()
    dest = dest.upper() if dest else None
    
    with get_status(f"[bold blue]Fetching live departures from {start}..."):
        if dest:
            url = f"https://huxley2.azurewebsites.net/departures/{start}/to/{dest}?expand=true"
        else:
            url = f"https://huxley2.azurewebsites.net/departures/{start}?expand=true"
            
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 400:
                console.print(f"[bold red]Invalid station code: {resp.text}[/bold red]")
                raise typer.Exit(1)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            console.print(f"[bold red]Failed to fetch departures: {e}[/bold red]")
            raise typer.Exit(1)

    services = data.get("trainServices", [])
    if not services:
        console.print(f"No services found from {start}" + (f" to {dest}" if dest else ""))
        return

    if is_piped:
        table = Table(title=f"Live: {start} -> {dest}" if dest else f"Live: {start}", box=box.SIMPLE)
        table.add_column("Dep")
        if dest:
            table.add_column("Arr")
        table.add_column("Dest")
    else:
        table = Table(title=f"Live Departures: {data.get('locationName')} " + (f"to {dest}" if dest else ""))
        table.add_column("Expected", style="cyan")
        table.add_column("Scheduled", style="blue")
        table.add_column("Destination", style="magenta")
        table.add_column("Platform", style="green")
        
        if dest:
            table.add_column(f"Arrives at {dest}", style="cyan")

    now = datetime.now()
    count = 0
    
    for s in services:
        std = s.get("std", "") # Scheduled Time of Departure
        etd = s.get("etd", "") # Expected Time of Departure
        
        # Calculate minutes until departure for travel buffer
        # Assume today. Handle crossing midnight later if needed, but live boards are usually < 2hrs anyway
        if std:
            try:
                departure_time = datetime.strptime(std, "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day
                )
                if departure_time < now - timedelta(hours=6):
                    # It crossed midnight to tomorrow
                    departure_time += timedelta(days=1)
                
                minutes_until = (departure_time - now).total_seconds() / 60
                if etd != "On time" and etd != "Cancelled" and etd != "Delayed" and ":" in etd:
                    # Parse actual estimated time if available
                    est_time = datetime.strptime(etd, "%H:%M").replace(
                        year=now.year, month=now.month, day=now.day
                    )
                    if est_time < now - timedelta(hours=6):
                        est_time += timedelta(days=1)
                    minutes_until_est = (est_time - now).total_seconds() / 60
                    # Use est if it's more accurate
                    minutes_until = minutes_until_est
                    
                if allow > 0 and minutes_until < allow:
                    continue # Skip this train
            except ValueError:
                pass # Parse error, just show it
        
        dest_name = s.get("destination", [{}])[0].get("locationName", "Unknown")
        plat = s.get("platform", "-") or "-"
        
        arrival_time = "-"
        if dest:
            sub_points = s.get("subsequentCallingPoints", [])
            if sub_points:
                for cp in sub_points[0].get("callingPoint", []):
                    if cp.get("crs") == dest:
                        st = cp.get("st", "")
                        et = cp.get("et", "")
                        arrival_time = et if et and et != "On time" else st
                        if et == "On time":
                            arrival_time = f"{st} (On time)"

        if is_piped:
            time_display = std if etd == "On time" else (etd if ":" in etd else std)
            if dest:
                arr_disp = arrival_time.replace(" (On time)", "")
                row = [time_display, arr_disp, dest_name[:10]]
            else:
                row = [time_display, dest_name[:14]]
        else:
            row = [etd, std, dest_name, plat]
            if dest:
                row.append(arrival_time)
            
        table.add_row(*row)
        count += 1
        if count >= 5:
            break

    if count == 0:
        console.print("[yellow]No trains found matching criteria.[/yellow]")
    else:
        console.print(table)


@app.command()
def journey(
    start: str = typer.Argument(..., help="Start station CRS code (e.g. VIC)"),
    dest: str = typer.Argument(..., help="Destination CRS code (e.g. BTN)"),
    date: str = typer.Option("today", help="Date in DDMMYY, 'today', or 'tomorrow'"),
    time: str = typer.Option(None, help="Time in HHMM (e.g., 1800). Defaults to now."),
    leave: bool = typer.Option(True, "--leave/--arrive", help="Whether time specified is leaving at or arriving by"),
    allow: int = typer.Option(0, "--allow", "-a", help="Travel buffer: allow X minutes travel, don't show trains sooner.")
):
    """
    Plan a journey and see times matching a specific date/time.
    """
    start = start.upper()
    dest = dest.upper()
    
    if not time:
        time = datetime.now().strftime("%H%M")
        
    dep_or_arr = "dep" if leave else "arr"
    
    url = f"https://ojp.nationalrail.co.uk/service/timesandfares/{start}/{dest}/{date}/{time}/{dep_or_arr}"

    with get_status("[bold blue]Planning Journey..."):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            console.print(f"[bold red]Failed to fetch journey plan: {e}[/bold red]")
            raise typer.Exit(1)
            
    # Extract JSON breakdown from the Javascript blocks within the OJP response
    matches = re.findall(r'"jsonJourneyBreakdown":\s*(\{.*?\})', html)
    
    if not matches:
        console.print(f"[yellow]No journeys found. Are station codes correct? Check: {url}[/yellow]")
        raise typer.Exit(1)

    if is_piped:
        table = Table(title=f"Timetable: {start} -> {dest}", box=box.SIMPLE)
        table.add_column("Dep")
        table.add_column("Arr")
        table.add_column("Dur")
    else:
        table = Table(title=f"Timetable: {start} -> {dest}")
        table.add_column("Departs", style="cyan")
        table.add_column("Arrives", style="blue")
        table.add_column("Duration", style="magenta")
        table.add_column("Changes", style="yellow")
        table.add_column("Status", style="green")

    now = datetime.now()
    count = 0
    # Create an arbitrary base date for calculating minutes diff if comparing strictly times
    # However OJP already handles time/date ordering, we just need to filter by travel buffer
    
    for m in matches:
        try:
            data = json.loads(m)
            dep_time_str = data.get('departureTime')
            arr_time_str = data.get('arrivalTime')
            h, m_mins = data.get('durationHours', 0), data.get('durationMinutes', 0)
            duration = f"{h}h {m_mins}m"
            changes = str(data.get('changes', 0))
            status = data.get('statusMessage', "")
            
            # Simple travel buffer check
            if allow > 0:
                dt = datetime.strptime(dep_time_str, "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day
                )
                # If we are searching for "today" and time is in the past, it could be valid for OJP
                # But we filter it if it's less than allow
                
                # Careful: if the user searched for 'tomorrow', now() is wrong base date.
                if date == "today":
                     # Adjust if it crosses midnight
                     if dt < now - timedelta(hours=6):
                         dt += timedelta(days=1)
                         
                     minutes_until = (dt - now).total_seconds() / 60
                     if minutes_until < allow:
                         continue
                
            if is_piped:
                table.add_row(dep_time_str, arr_time_str, duration)
            else:
                table.add_row(dep_time_str, arr_time_str, duration, changes, status)
            count += 1
            if count >= 5:
                break
        except json.JSONDecodeError:
            continue
            
    if count == 0:
        console.print("[yellow]No trains found matching criteria after buffer filter.[/yellow]")
    else:
        console.print(table)


if __name__ == "__main__":
    app()
