import click


@click.group()
def skill() -> None:
    """Skill script commands (audit, notify, permission, release-notes)."""
