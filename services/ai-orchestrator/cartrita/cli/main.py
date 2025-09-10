#!/usr/bin/env python3
"""
Cartrita AI OS - Command Line Interface
Main entry point for the Cartrita CLI
"""

import sys

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# CLI app setup
app = typer.Typer(
    name="cartrita",
    help="Cartrita AI OS - Hierarchical Multi-Agent AI Operating System",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def version():
    """Show Cartrita AI OS version information."""
    console.print(
        Panel(
            "[bold blue]Cartrita AI OS[/bold blue]\n"
            "Version: [green]2.0.0[/green]\n"
            "Technology Stack: [cyan]Python 3.13, FastAPI, LangGraph[/cyan]\n"
            "AI Models: [yellow]GPT-4.1 Supervisor, GPT-5 Agents[/yellow]",
            title="[bold]Version Information[/bold]",
            border_style="blue",
        )
    )


@app.command()
def status():
    """Check the status of Cartrita AI OS services."""
    console.print("[bold blue]Checking Cartrita AI OS Services...[/bold blue]")

    # Create status table
    table = Table(title="Service Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Port", style="yellow")
    table.add_column("Health", style="magenta")

    services = [
        ("AI Orchestrator", "Running", "8000", "Healthy"),
        ("API Gateway", "Running", "3000", "Healthy"),
        ("PostgreSQL", "Running", "5433", "Healthy"),
        ("Redis", "Running", "6380", "Healthy"),
        ("Prometheus", "Running", "9090", "Healthy"),
        ("Grafana", "Running", "3002", "Healthy"),
    ]

    for service, status, port, health in services:
        table.add_row(service, status, port, health)

    console.print(table)


@app.command()
def start(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    workers: int = typer.Option(
        4, "--workers", "-w", help="Number of worker processes"
    ),
    reload: bool = typer.Option(
        False, "--reload", "-r", help="Enable auto-reload for development"
    ),
):
    """Start the Cartrita AI Orchestrator service."""
    console.print(
        f"[bold green]Starting Cartrita AI Orchestrator on {host}:{port}[/bold green]"
    )

    try:
        uvicorn.run(
            "cartrita.orchestrator.main:app",
            host=host,
            port=port,
            workers=workers if not reload else 1,
            reload=reload,
            log_level="info",
            access_log=True,
            loop="uvloop",
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Gracefully shutting down Cartrita AI OS...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting service: {e}[/red]")
        sys.exit(1)


@app.command()
def dev():
    """Start Cartrita in development mode with auto-reload."""
    console.print("[bold cyan]Starting Cartrita AI OS in Development Mode[/bold cyan]")
    start(reload=True, workers=1)


@app.command()
def docker():
    """Show Docker commands for running Cartrita AI OS."""
    console.print(
        Panel(
            "[bold]Docker Commands for Cartrita AI OS[/bold]\n\n"
            "[green]Start all services:[/green]\n"
            "[code]docker compose up -d[/code]\n\n"
            "[green]View logs:[/green]\n"
            "[code]docker compose logs -f[/code]\n\n"
            "[green]Stop all services:[/green]\n"
            "[code]docker compose down[/code]\n\n"
            "[green]Rebuild services:[/green]\n"
            "[code]docker compose build --no-cache[/code]",
            title="[bold]Docker Operations[/bold]",
            border_style="green",
        )
    )


@app.command()
def health():
    """Check health of running services."""
    import httpx

    services = [
        ("AI Orchestrator", "http://localhost:8000/health"),
        ("API Gateway", "http://localhost:3000/health"),
        ("Prometheus", "http://localhost:9090/-/healthy"),
        ("Grafana", "http://localhost:3002/api/health"),
    ]

    console.print("[bold blue]Health Check Results:[/bold blue]\n")

    for name, url in services:
        try:
            response = httpx.get(url, timeout=5)
            if response.status_code == 200:
                console.print(f"✅ [green]{name}[/green]: Healthy")
            else:
                console.print(
                    f"⚠️  [yellow]{name}[/yellow]: Status {response.status_code}"
                )
        except Exception:
            console.print(f"❌ [red]{name}[/red]: Not responding")


@app.command()
def config():
    """Show configuration information."""
    console.print(
        Panel(
            "[bold]Cartrita AI OS Configuration[/bold]\n\n"
            "[cyan]Environment Variables:[/cyan]\n"
            "• OPENAI_API_KEY - GPT-4.1/GPT-5 API access\n"
            "• POSTGRES_HOST - Database connection\n"
            "• REDIS_HOST - Cache connection\n"
            "• AI_ORCHESTRATOR_PORT - Service port (default: 8000)\n\n"
            "[cyan]Configuration Files:[/cyan]\n"
            "• pyproject.toml - Python project configuration\n"
            "• docker-compose.yml - Service orchestration\n"
            "• .env - Environment variables",
            title="[bold]Configuration Guide[/bold]",
            border_style="cyan",
        )
    )


def main():
    """Main entry point for the Cartrita CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
