# SPDX-FileCopyrightText: 2023 Brian Kubisiak <brian@kubisiak.com>
#
# SPDX-License-Identifier: GPL-3.0-only

"""User interface for viewing/manipulating the birdr database."""

import datetime
import pathlib
import sys
import typing as T

import click

from birdr import controller


@click.group()
def main() -> None:
    """Record and track bird sightings."""


@main.command()
@click.argument("ebird_list", required=False, type=click.Path(exists=True))
def init(ebird_list: str = None) -> None:
    """Initialize the bird database.

    Optionally, use the given EBIRD_LIST (downloaded from ebird.org) to
    populate the species and category databases.
    """
    ebird_path = pathlib.Path(ebird_list) if ebird_list else None
    controller.init(ebird_list=ebird_path)


@main.command()
@click.option(
    "--non-interactive",
    "-n",
    is_flag=True,
    help="Parse sighting data from stdin instead of prompting.",
)
def add(non_interactive: bool = False) -> None:
    """Add a new series of sightings to the database.

    Sightings may be added either interactively or non-interactively. When
    adding interactively, a series of sightings are added for a single date and
    location. Species names are prompted; notes are read using $EDITOR.

    When adding non-interactively, sighting data is read through stdin. Each
    line is a single entry containing the date (in YYYY/MM/DD format),
    location, species name, and notes (all separated by nil characters).
    """
    if non_interactive:
        _add_non_interactive()
    else:
        _add_interactive()


def _add_non_interactive() -> None:
    for line in sys.stdin:
        [date_str, location, species, notes] = line.strip().split("\0")
        date = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()
        controller.add(
            date=date, location=location, species=species, notes=notes
        )


def _add_interactive() -> None:
    raise NotImplementedError()


class InputIterator:
    """Iterate over input using the given prompt."""

    def __init__(self, prompt: str) -> None:
        """Create a new input interator using the given prompt."""
        self.prompt = prompt

    def __iter__(self) -> T.Iterator[str]:
        """Get the iterator object."""
        return self

    def __next__(self) -> str:
        """Get the next prompted entry from the input."""
        try:
            return input(self.prompt).strip()
        except EOFError as exc:
            raise StopIteration from exc


@main.command()
@click.argument("name", required=True)
def checklist(name: str) -> None:
    """Add a new checklist to the database."""
    controller.create_checklist(name=name, species=InputIterator("species? "))
