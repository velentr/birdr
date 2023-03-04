# SPDX-FileCopyrightText: 2023 Brian Kubisiak <brian@kubisiak.com>
#
# SPDX-License-Identifier: GPL-3.0-only

"""User interface for viewing/manipulating the birdr database."""

import pathlib

import click

from birdr import controller


@click.group()
def main() -> None:
    """Record and track bird sightings."""


@main.command()
@click.argument("ebird_list", required=False)
def init(ebird_list: str = None) -> None:
    """Initialize the bird database.

    Optionally, use the given EBIRD_LIST (downloaded from ebird.org) to
    populate the species and category databases.
    """
    ebird_path = pathlib.Path(ebird_list) if ebird_list else None
    controller.init(ebird_list=ebird_path)
