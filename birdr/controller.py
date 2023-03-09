# SPDX-FileCopyrightText: 2023 Brian Kubisiak <brian@kubisiak.com>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Policy for interacting with the user's system."""

import datetime
import os
import pathlib

from birdr.model import Model


def get_database_path() -> pathlib.Path:
    """Get the path to the user's local database file."""
    return (
        pathlib.Path(
            os.environ.get(
                "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
            )
        )
        / "birdr/birds.db"
    )


def init(*, ebird_list: pathlib.Path = None) -> None:
    """Initialize the bird database."""
    eng = Model(get_database_path())
    eng.create()

    if ebird_list is not None:
        with ebird_list.open("r") as filp, eng.transaction() as transaction:
            transaction.load_ebird_list(filp)


def add(
    *, date: datetime.date, location: str, species: str, notes: str
) -> None:
    """Add a new sighting to the database."""
    with Model(get_database_path()).transaction() as transaction:
        transaction.add_sighting(date, species, location, notes)
