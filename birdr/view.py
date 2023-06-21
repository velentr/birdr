# SPDX-FileCopyrightText: 2023 Brian Kubisiak <brian@kubisiak.com>
#
# SPDX-License-Identifier: GPL-3.0-only

"""User interface for viewing/manipulating the birdr database."""

import datetime
import logging
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import typing as T

import click
import rich
import rich.tree

from birdr import controller

VERSION = "0.0.0"


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


def _parse_date(date_str: str) -> datetime.date:
    return datetime.datetime.strptime(date_str, "%Y/%m/%d").date()


def _add_non_interactive() -> None:
    for line in sys.stdin:
        [date_str, location, species, notes] = line.strip().split("\0")
        date = _parse_date(date_str)
        controller.add(
            date=date, location=location, species=species, notes=notes
        )


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


class ObservationIterator:
    """Iterate over input to generate observations."""

    def __init__(self, date: datetime.date, location: str) -> None:
        """Create a new iterator for generating observations."""
        self.date = date
        self.location = location
        self.input_iter = iter(InputIterator("species? "))
        self.editor = os.environ.get("EDITOR", "vi")
        self.whitespace_sub = re.compile(r"\s+")

    def __iter__(self) -> T.Iterator[T.Tuple[datetime.date, str, str, str]]:
        """Get the iterator object."""
        return self

    def __next__(self) -> T.Tuple[datetime.date, str, str, str]:
        """Get the next observation."""
        species = next(self.input_iter)

        with tempfile.NamedTemporaryFile(mode="r") as notes_file:
            result = subprocess.call([self.editor, notes_file.name])
            if result != 0:
                logging.error(
                    "%s exited unsuccessfully; aborting", self.editor
                )
                raise StopIteration

            notes = re.sub(self.whitespace_sub, " ", notes_file.read()).strip()
            if not notes:
                raise StopIteration

        return (self.date, self.location, species, notes)


def _add_interactive() -> None:
    date_str = input("date? ")
    try:
        date = _parse_date(date_str)
    except ValueError:
        logging.error("%s is not a valid date", date_str)
        sys.exit(1)

    location = input("location? ")

    controller.add_observations(
        observations=ObservationIterator(date, location)
    )


@main.command()
@click.argument("name", required=True)
def checklist(name: str) -> None:
    """Add a new checklist to the database."""
    controller.create_checklist(name=name, species=InputIterator("species? "))


@main.command()
@click.argument("checklist_name", required=True)
def show(checklist_name: str) -> None:
    """Show the status of a checklist."""
    data = controller.get_checklist_data(checklist=checklist_name)

    if data is None:
        logging.error("%s is not a valid checklist", checklist_name)
        sys.exit(1)

    tree = rich.tree.Tree(f"{data.complete:4.0%} {checklist_name}")
    for category, cat_data in sorted(data.categories.items()):
        branch = tree.add(f"{cat_data.complete:4.0%} {category}")
        for species in sorted(cat_data.seen | cat_data.unseen):
            mark = (
                "[green]:heavy_check_mark:[/green]"
                if species in cat_data.seen
                else "[black]:black_medium_square:[/black]"
            )
            branch.add(f"{mark} {species}")

    rich.print(tree)


@main.command()
def version() -> None:
    """Check the version number of the application."""
    print(f"birdr v{VERSION}")
