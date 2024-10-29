from datetime import datetime
import typer


def log_prefix() -> str:
    return f"{datetime.now().strftime("%c")} "


def info(msg):
    typer.echo(
        log_prefix() + typer.style(
            msg,
            fg=typer.colors.GREEN,
            bold=True
        ),
        err=False
    )


def error(msg: str):
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
