# SPDX-FileCopyrightText: 2023 Brian Kubisiak <brian@kubisiak.com>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Data model for the birdr database."""
import contextlib
import csv
import datetime
import dataclasses
import pathlib
import typing as T

import sqlalchemy
from sqlalchemy.orm import declarative_base, relationship, session


Base = declarative_base()


class Species(Base):
    """Table holding the full species list."""

    __tablename__ = "species"

    # TODO: typing information with sqlalchemy-2.0
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    category_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("category.id")
    )

    category = relationship("Category", back_populates="species")
    sightings = relationship("Sighting", back_populates="species")
    checklists = relationship(
        "Checklist", secondary="species_checklist", back_populates="species"
    )


class Category(Base):
    """Table holding general non-scientific groupings for bird species."""

    __tablename__ = "category"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)

    species = relationship("Species", back_populates="category")


class Sighting(Base):
    """Table holding all bird sightings."""

    __tablename__ = "sightings"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    year = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    month = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    day = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    location = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    species_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("species.id")
    )
    notes = sqlalchemy.Column(sqlalchemy.String)

    species = relationship("Species", back_populates="sightings")


class Checklist(Base):
    """Table holding checklist information."""

    __tablename__ = "checklist"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)

    species = relationship(
        "Species", secondary="species_checklist", back_populates="checklists"
    )


class SpeciesChecklist(Base):
    """Table bridging checklists with species.

    Generally, this should not be used directly. The Species and Checklist
    tables should back populate each other through this bridge.
    """

    __tablename__ = "species_checklist"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    species_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("species.id")
    )
    checklist_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("checklist.id")
    )


class UnrecognizedSpecies(Exception):
    """An unrecognized species was found."""


@dataclasses.dataclass(frozen=True)
class Transaction:
    """Interface to a database that lets you manipulate the tables."""

    session: session.Session

    def lookup_checklist(
        self, checklist_name: str
    ) -> T.Optional[T.Iterator[T.Tuple[str, str, bool]]]:
        """Iterate through all species in a checklist."""
        checklist = self._lookup_checklist_by_name(checklist_name)
        if checklist is None:
            return None

        return map(
            lambda species: (
                species.name,
                species.category.name,
                len(species.sightings) > 0,
            ),
            checklist.species,
        )

    def lookup_checklist_names(self) -> T.Iterator[str]:
        """Iterate through all the checklists in the database."""
        return map(
            lambda checklist: checklist.name, self.session.query(Checklist)
        )

    def load_ebird_list(self, ebird_list: T.TextIO) -> None:
        """Load the ebird species list."""
        categories: T.Dict[str, Category] = {}
        csv_input = csv.reader(ebird_list)

        # Note that the first line is the header; we are implicitly ignoring it
        # with the 'species' check below.
        for csv_line in csv_input:
            if csv_line[1] != "species":
                continue
            name = csv_line[3]
            category_name = csv_line[7]

            if category_name in categories:
                category = categories[category_name]
            else:
                category = Category(name=category_name)
                categories[category_name] = category

            species = Species(name=name, category=category)

            self.session.add(species)

    def _lookup_species_by_name(self, species: str) -> sqlalchemy.orm.Query:
        """Lookup SPECIES in the database, ordered alphabetically by name."""
        return (
            self.session.query(Species)
            .filter(Species.name.like(species))
            .order_by(Species.name)
        )

    def _lookup_one_species_by_name(self, species: str) -> T.Optional[Species]:
        """Lookup a species by name."""
        return self._lookup_species_by_name(species).one_or_none()

    def lookup_matching_species(self, prefix: str) -> T.Iterable[Species]:
        """Look up all the species that match the given PREFIX."""
        return self._lookup_species_by_name(f"{prefix}%")

    def add_sighting(
        self, date: datetime.date, species: str, location: str, notes: str
    ) -> None:
        """Add a new bird sighting in the database."""
        species_obj = self._lookup_one_species_by_name(species)
        if species_obj is None:
            raise UnrecognizedSpecies(species)

        sighting = Sighting(
            year=date.year,
            month=date.month,
            day=date.day,
            location=location,
            species=species_obj,
            notes=notes,
        )
        self.session.add(sighting)

    def add_checklist(self, name: str) -> None:
        """Create a new checklist in the database."""
        checklist = Checklist(name=name)
        self.session.add(checklist)

    def _lookup_checklist_by_name(self, checklist: str) -> Checklist:
        """Lookup SPECIES in the database, ordered alphabetically by name."""
        return (
            self.session.query(Checklist)
            .filter(Checklist.name == checklist)
            .one_or_none()
        )

    def add_species_to_checklist(self, checklist: str, species: str) -> bool:
        """Add an existing species to a checklist.

        Return True if the species was added successfully; False is it was not.
        """
        checklist_obj = self._lookup_checklist_by_name(checklist)
        if checklist_obj is None:
            return False

        species_obj = self._lookup_one_species_by_name(species)
        if species_obj is None:
            return False

        species_obj.checklists.append(checklist_obj)
        return True


class Model:
    """Main class for interfacing with the data model of birdr."""

    def __init__(self, path: pathlib.Path) -> None:
        """Initialize the engine for a new model interface."""
        # TODO: remove future once on sqlalchemy-2.0
        self.path = path
        self.engine = sqlalchemy.create_engine(
            f"sqlite+pysqlite:///{str(path)}", future=True
        )

    def create(self) -> None:
        """Create the tables in the database if necessary."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self.engine)

    @contextlib.contextmanager
    def transaction(self) -> T.Iterator[Transaction]:
        """Start a group of operations on a database.

        If any operation fails, none of the operations will be committed.
        """
        with session.Session(self.engine) as sess:
            yield Transaction(session=sess)
            sess.commit()
