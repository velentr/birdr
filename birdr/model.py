# SPDX-FileCopyrightText: 2023 Brian Kubisiak <brian@kubisiak.com>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Data model for the birdr database."""
import csv
import datetime
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


class UnrecognizedSpecies(Exception):
    """An unrecognized species was found."""


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

    def load_ebird_list(self, ebird_list: T.TextIO) -> None:
        """Load the ebird species list."""
        categories: T.Dict[str, Category] = {}
        csv_input = csv.reader(ebird_list)

        with session.Session(self.engine) as sess:
            # Note that the first line is the header; we are implicitly
            # ignoring it with the 'species' check below.
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

                sess.add(species)

            sess.commit()

    def add_sighting(
        self, date: datetime.date, species: str, location: str, notes: str
    ) -> None:
        """Add a new bird sighting in the database."""
        with session.Session(self.engine) as sess:
            query = sqlalchemy.select(Species).filter(
                Species.name.like(f"{species}")
            )
            species_obj = sess.execute(query).scalars().one_or_none()
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
            sess.add(sighting)
            sess.commit()
