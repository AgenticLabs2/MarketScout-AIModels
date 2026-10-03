import click
import sys
from rich.console import Console

from src.cli.tui.app import MarketScoutApp

console = Console()

@click.command(name="tui")
def tui_command():
    """Launch the Terminal User Interface"""
    try:
        # Clear console on startup
        console.clear()
        console.print("[bold blue]Starting MarketScout TUI...[/bold blue]")
        
        app = MarketScoutApp()
        app.run()
        
        # Clear console on normal exit
        console.clear()
    except KeyboardInterrupt:
        console.clear()
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        console.clear()
        console.print(f"[red]TUI Error: {e}[/red]")
        sys.exit(1)
