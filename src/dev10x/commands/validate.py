import click


@click.group()
def validate() -> None:
    """Direct validator access for testing."""
