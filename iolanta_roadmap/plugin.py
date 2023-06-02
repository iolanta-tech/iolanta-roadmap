from typing import Optional

from iolanta import Plugin
from typer import Typer

from iolanta_roadmap.cli import roadmap_cli


class Roadmap(Plugin):
    """Draw a roadmap."""

    typer_app = roadmap_cli
