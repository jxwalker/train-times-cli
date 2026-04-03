# 🚆 UK Train Times CLI & Label Printer

A beautiful, terminal-first CLI application to check UK train times, live departures, and London Underground status.

What makes this project special? It was meticulously designed to **support perfect pipeline outputs to 3-inch thermal sticky note printers** (such as the Nemonic Label printer) directly from macOS and Linux CUPS queues without any extra parsing.

## ✨ Features

- **Live Departures**: Query the National Rail Darwin API (via the open-source Huxley 2 proxy) to get exactly what's on the board right now.
- **Journey Planner**: Scrape National Rail Enquiries (OJP) directly for future or past timetables without needing an expensive commercial API key.
- **Tube Status**: Ping the Transport for London (TfL) Unified API to check if any Tube lines have closures or severe delays.
- **Label Printer Support**: Automatically detects when its output is being piped to a secondary program (like `lpr`) and tightly formats the text to exactly 32-characters wide, removing all ANSI color codes so your physical 3x3 inch thermal sticky notes print perfectly!
- **Travel Buffers**: Easily factor in your walk to the station. Use the `--allow 10` flag to hide trains leaving in the next 10 minutes so you only evaluate trains you can actually catch.

## 📦 Installation

This CLI requires **Python 3**.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jxwalker/train-times-cli.git
   cd train-times-cli
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🛠 Usage

Ensure you are inside your virtual environment whenever you want to use the CLI (`source venv/bin/activate`).
Alternatively, set up a bash alias in your `~/.zshrc`:
```bash
alias trains="source ~/path/to/train-times-cli/venv/bin/activate && python ~/path/to/train-times-cli/train_cli.py"
```

### 1. Live Departures
Get the next 5 trains departing from a specific station.

```bash
# Fetch live departures from Harpenden (HPD) to London Victoria (VIC)
python train_cli.py live HPD VIC

# Add a 10 Minute walking buffer so we don't sprint to a train we can't make!
python train_cli.py live HPD VIC -a 10 
```

### 2. Journey Planner
Search the timetable for journeys.

```bash
# Show trains from Victoria to Brighton leaving around 13:00 today
python train_cli.py journey VIC BTN --time 1300 --leave

# Show trains arriving in Brighton tomorrow by 09:00 AM
python train_cli.py journey VIC BTN --date tomorrow --time 0900 --arrive 
```

### 3. London Underground Status
Check the TfL network for delays.

```bash
python train_cli.py tube
```

## 🖨️ Printing to Nemonic (or other Label Printers)

You can pass the output directly to a CUPS print queue using the `lpr` daemon. The script will automatically auto-adjust its formatting for print media whenever you pipe it.

```bash
# Send current train plans right to the physical label printer Queue!
python train_cli.py journey HPD CTK -a 10 | lpr -P Nemonic_MIP_201
```

*(Note: If you have a different label printer, just replace `Nemonic_MIP_201` with your printer's CUPS Queue name, which can be found via `lpstat -a`)*.
## 🛠 Usage

Ensure you are inside your virtual environment whenever you want to use the CLI (`source venv/bin/activate`).
Alternatively, set up a bash alias in your `~/.zshrc`:
```bash
alias trains="source ~/path/to/train-times-cli/venv/bin/activate && python ~/path/to/train-times-cli/train_cli.py"
```

### Main CLI Command
```
Usage: train_cli.py [OPTIONS] COMMAND [ARGS]...                
                                                                
 UK Train Times and London Underground CLI                      
                                                                
╭─ Options ────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the     │
│                               current shell.                 │
│ --show-completion             Show completion for the        │
│                               current shell, to copy it or   │
│                               customize the installation.    │
│ --help                        Show this message and exit.    │
╰──────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────╮
│ tube     Check for any problems on the London Underground    │
│          network.                                            │
│ live     Fetch the live departure board for a station.       │
│ journey  Plan a journey and see times matching a specific    │
│          date/time.                                          │
╰──────────────────────────────────────────────────────────────╯
```

### 1. Live Departures (`live`)
Get the next 5 trains departing from a specific station.

```
Usage: train_cli.py live [OPTIONS] START [DEST]                
                                                                
 Fetch the live departure board for a station.                  
                                                                
╭─ Arguments ──────────────────────────────────────────────────╮
│ *    start      TEXT    Start station CRS code (e.g. VIC)    │
│                         [required]                           │
│      dest       [DEST]  Optional destination CRS code (e.g.  │
│                         BTN)                                 │
╰──────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────╮
│ --allow  -a      INTEGER  Travel buffer: allow X minutes     │
│                           travel to station, don't show      │
│                           trains before this.                │
│                           [default: 0]                       │
│ --help                    Show this message and exit.        │
╰──────────────────────────────────────────────────────────────╯
```
**Examples:**
```bash
# Fetch live departures from Harpenden (HPD) to London Victoria (VIC)
python train_cli.py live HPD VIC

# Add a 10 Minute walking buffer so we don't sprint to a train we can't make!
python train_cli.py live HPD VIC -a 10 
```

### 2. Journey Planner (`journey`)
Search the timetable for journeys.

```
Usage: train_cli.py journey [OPTIONS] START DEST               
                                                                
 Plan a journey and see times matching a specific date/time.    
                                                                
╭─ Arguments ──────────────────────────────────────────────────╮
│ *    start      TEXT  Start station CRS code (e.g. VIC)      │
│                       [required]                             │
│ *    dest       TEXT  Destination CRS code (e.g. BTN)        │
│                       [required]                             │
╰──────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────╮
│ --date                   TEXT     Date in DDMMYY, 'today',   │
│                                   or 'tomorrow'              │
│                                   [default: today]           │
│ --time                   TEXT     Time in HHMM (e.g., 1800). │
│                                   Defaults to now.           │
│ --leave      --arrive             Whether time specified is  │
│                                   leaving at or arriving by  │
│                                   [default: leave]           │
│ --allow  -a              INTEGER  Travel buffer: allow X     │
│                                   minutes travel, don't show │
│                                   trains sooner.             │
│                                   [default: 0]               │
│ --help                            Show this message and      │
│                                   exit.                      │
╰──────────────────────────────────────────────────────────────╯
```
**Examples:**
```bash
# Show trains from Victoria to Brighton leaving around 13:00 today
python train_cli.py journey VIC BTN --time 1300 --leave

# Show trains arriving in Brighton tomorrow by 09:00 AM
python train_cli.py journey VIC BTN --date tomorrow --time 0900 --arrive 
```

### 3. London Underground Status (`tube`)
Check the TfL network for delays.

```
Usage: train_cli.py tube [OPTIONS]                             
                                                                
 Check for any problems on the London Underground network.      
                                                                
╭─ Options ────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────╯
```
**Examples:**
```bash
python train_cli.py tube
```

## 🖨️ Printing to Nemonic (or other Label Printers)

You can pass the output directly to a CUPS print queue using the `lpr` daemon. The script will automatically auto-adjust its formatting for print media whenever you pipe it.

```bash
# Send current train plans right to the physical label printer Queue!
python train_cli.py journey HPD CTK -a 10 | lpr -P Nemonic_MIP_201
```

*(Note: If you have a different label printer, just replace `Nemonic_MIP_201` with your printer's CUPS Queue name, which can be found via `lpstat -a`)*.
