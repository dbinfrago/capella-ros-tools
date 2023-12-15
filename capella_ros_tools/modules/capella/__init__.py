# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Capella model definition."""
import typing as t

import capellambse


class EnumValue(t.NamedTuple):
    """Capella enum value."""

    type: str
    name: str
    value: int
    description: str


class EnumDef(t.NamedTuple):
    """Capella enum."""

    name: str
    values: list[EnumValue]
    description: str


class ClassProperty(t.NamedTuple):
    """Capella class property."""

    type_name: str
    type_pkg_name: str
    name: str
    min_card: float
    max_card: float
    description: str


class ClassDef(t.NamedTuple):
    """Capella class."""

    name: str
    properties: list[ClassProperty]
    description: str


class BaseCapellaModel:
    """Base class for capella model."""

    def __init__(
        self,
        path_to_capella_model: str,
        layer: str,
    ) -> None:
        self.model = capellambse.MelodyModel(path_to_capella_model)
        self.data = getattr(self.model, layer).data_package
        self.predef_types = self.model.sa.data_package.packages.by_name(
            "Predefined Types"
        ).datatypes
