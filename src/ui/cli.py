"""Terminal-based chat interface using Rich."""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text

from src.agent.orchestrator import Orchestrator


def run_cli():
    """Run the chatbot in CLI mode."""
    console = Console()
    agent = Orchestrator()

    console.print(Panel.fit(
        "[bold blue]🤖 Trenkwalder HR Chatbot[/bold blue]\n"
        "[dim]Ask me about company policies, benefits, vacation days, and more![/dim]\n"
        "[dim]Type 'quit' or 'exit' to stop. Type 'reset' to clear history.[/dim]",
        border_style="blue",
    ))
    console.print()

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye! 👋[/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye! 👋[/dim]")
            break

        if user_input.lower() == "reset":
            agent.reset()
            console.print("[dim]Conversation reset.[/dim]\n")
            continue

        # Show spinner while processing
        with console.status("[bold blue]Thinking...", spinner="dots"):
            try:
                response = agent.chat(user_input)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]\n")
                continue

        console.print()
        console.print(Panel(
            Markdown(response),
            title="[bold blue]🤖 Assistant[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        ))
        console.print()
