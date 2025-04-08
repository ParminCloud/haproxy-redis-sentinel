from datetime import datetime
import typer


def log_prefix() -> str:
    """
    Returns a formatted string with the current date and time.
    """
    return f"{datetime.now().strftime('%c')} "


def info(msg: str):
    """
    Prints an info message with a green color.
        :param msg: Message to print
    """
    typer.echo(
        log_prefix() + typer.style(
            msg,
            fg=typer.colors.GREEN,
            bold=True
        ),
        err=False
    )


def error(msg: str):
    """
    Prints an error message with a red color.
        :param msg: Message to print
    """
    typer.echo(
        log_prefix() + typer.style(
            msg,
            fg=typer.colors.WHITE,
            bg=typer.colors.RED,
            bold=True
        ),
        err=True
    )


__all__ = ["info", "error"]
