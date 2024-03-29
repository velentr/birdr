# SPDX-FileCopyrightText: 2023 Brian Kubisiak <brian@kubisiak.com>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Policy for interacting with the user's system."""

from __future__ import annotations

import dataclasses
import datetime
import os
import pathlib
import readline
import typing as T

from birdr.model import Model, Species, Transaction


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


def init(*, ebird_list: T.Optional[pathlib.Path] = None) -> None:
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


class SpeciesCompleter:
    """Readline tab completion engine for species."""

    def __init__(self, transaction: Transaction) -> None:
        """Initialize the engine using the given transaction."""
        self.transaction = transaction
        self.current: T.Optional[T.Iterator[Species]] = None

    def readline_completer(self, text: str, state: int) -> T.Optional[str]:
        """Complete the given text line by query the database."""
        if state == 0:
            self.current = iter(self.transaction.lookup_matching_species(text))
        assert self.current is not None
        species = next(self.current)
        if species is None:
            return None
        return species.name

    def __enter__(self) -> None:
        """Activate this readline completion engine in a context."""
        readline.parse_and_bind("tab: complete")
        readline.set_completer_delims("")
        readline.set_completer(self.readline_completer)

    def __exit__(self, *_excinfo: T.Any) -> None:
        """De-activate the completion engine on exit."""
        readline.set_completer(None)


def add_observations(
    *, observations: T.Iterable[T.Tuple[datetime.date, str, str, str]]
) -> None:
    """Add a sequence of observations from the given iterator."""
    with Model(
        get_database_path()
    ).transaction() as transaction, SpeciesCompleter(transaction):
        for (date, location, species, notes) in observations:
            transaction.add_sighting(date, species, location, notes)


def create_checklist(*, name: str, species: T.Iterable[str]) -> None:
    """Create a new checklist in the database."""
    with Model(
        get_database_path()
    ).transaction() as transaction, SpeciesCompleter(transaction):
        transaction.add_checklist(name)
        for spec in species:
            transaction.add_species_to_checklist(name, spec)


def get_checklists() -> T.Iterator[str]:
    """Get the names of all checklists in the database."""
    with Model(get_database_path()).transaction() as transaction:
        for checklist in transaction.lookup_checklist_names():
            yield checklist


@dataclasses.dataclass(frozen=True)
class CategoryData:
    """High-level representation of a category of birds."""

    seen: T.Set[str]
    unseen: T.Set[str]
    complete: float = 0.0

    def add_seen(self, species: str) -> CategoryData:
        """Return a new category data with an additional observed species."""
        return CategoryData(
            seen=self.seen | {species},
            unseen=self.unseen,
            complete=(len(self.seen) + 1)
            / (len(self.seen) + len(self.unseen) + 1),
        )

    def add_unseen(self, species: str) -> CategoryData:
        """Return a new category data with an additional unobserved species."""
        return CategoryData(
            seen=self.seen,
            unseen=self.unseen | {species},
            complete=len(self.seen) / (len(self.seen) + len(self.unseen) + 1),
        )


@dataclasses.dataclass(frozen=True)
class ChecklistData:
    """High-level representation of a set of species (grouped by category)."""

    categories: T.Dict[str, CategoryData]
    complete: float = 0.0


def get_checklist_data(*, checklist: str) -> T.Optional[ChecklistData]:
    """Get structured data for a given checklist."""
    with Model(get_database_path()).transaction() as transaction:
        num_seen = 0
        num_total = 0
        categories: T.Dict[str, CategoryData] = {}

        checklist_data = transaction.lookup_checklist(checklist)
        if checklist_data is None:
            return None

        for (species, category, seen) in checklist_data:
            category_data = categories.get(category) or CategoryData(
                set(), set()
            )
            new_category = (
                category_data.add_seen(species)
                if seen
                else category_data.add_unseen(species)
            )
            categories[category] = new_category

            num_total += 1
            if seen:
                num_seen += 1

        return ChecklistData(
            categories=categories, complete=num_seen / num_total
        )
