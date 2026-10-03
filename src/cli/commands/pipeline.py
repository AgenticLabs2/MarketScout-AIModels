import click
import base64
import json
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.json import JSON

from src.pipeline.pipeline import resume_pipeline, run_linear_pipeline

console = Console()

@click.command(name="pipeline")
@click.argument('company_name')
@click.option('--domain', help='Specific domain to analyze (optional)')
@click.option('--output', '-o', help='Output file path for results')
@click.option('--format', 'output_format', default='json', 
              type=click.Choice(['json', 'markdown', 'pdf']), 
              help='Output format')
def pipeline_command(company_name: str, domain: Optional[str], output: Optional[str], output_format: str):
    """Run the complete market research pipeline"""
    
    console.print(f"[blue]Starting market research pipeline for: {company_name}[/blue]")
    
    if domain:
        console.print(f"[blue]Analyzing domain: {domain}[/blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Running pipeline...", total=None)
        
        try:
            # Run the pipeline
            result = run_linear_pipeline(company_name, domain)

            if result.get("status") == "interrupted":
                progress.stop()
                options = result["interrupt"]["options"]
                for index, option in enumerate(options, start=1):
                    console.print(f"[cyan]{index}.[/cyan] {option['domain']} ({option['score']:.2f})")
                selection = click.prompt("Select a domain", type=click.IntRange(1, len(options)), default=1)
                result = resume_pipeline(result["thread_id"], selection)
            
            if result.get('success'):
                console.print("[green]✓ Pipeline completed successfully![/green]")
                
                # Save output if specified
                if output:
                    output_path = Path(output)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if output_format == 'json':
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(result, f, indent=2)
                    elif output_format == 'markdown':
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(json.dumps(result, indent=2))
                    elif output_format == 'pdf':
                        encoded = result.get("data", {}).get("report_data", {}).get("pdf_content")
                        if not encoded:
                            raise click.ClickException("The graph completed without PDF content")
                        output_path.write_bytes(base64.b64decode(encoded))
                    
                    console.print(f"[green]Results saved to: {output_path}[/green]")
                else:
                    # Display results in console
                    console.print("\n[bold]Pipeline Results:[/bold]")
                    console.print(JSON(json.dumps(result, indent=2)))
                    
            else:
                console.print("[red]✗ Pipeline failed![/red]")
                console.print(f"[red]Errors: {', '.join(result.get('errors', ['Unknown error']))}[/red]")
                sys.exit(1)
                
        except Exception as e:
            console.print(f"[red]✗ Pipeline error: {e}[/red]")
            sys.exit(1)
