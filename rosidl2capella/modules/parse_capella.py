# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Class definition for Capella model parser."""
import typing as t

from . import BaseCapella, EnumValue, MsgProp


class ParseCapella(BaseCapella):
    """Parser for Capella model."""

    def get_packages(self, package: t.Any) -> set[str]:
        """Get packages in Capella model."""
        return {pkg.name for pkg in package.packages}

    def get_classes(self, package: t.Any) -> dict[str, t.Any]:
        """Get classes in Capella model."""
        classes: dict = {}
        for cls in package.classes:
            props = [
                MsgProp(
                    prop.name,
                    prop.type.name,
                    "",
                    prop.min_card.value,
                    prop.max_card.value,
                    prop.description,
                )
                for prop in cls.owned_properties
            ]
            classes[cls.name] = (cls.description, props)
        return classes

    def get_types(self, package: t.Any) -> dict[str, t.Any]:
        """Get types in Capella model."""
        types: dict = {}
        for type in package.datatypes:
            props = [
                EnumValue(
                    prop.name,
                    prop.type.name,
                    prop.value.value,
                    prop.description,
                )
                for prop in type.owned_literals
            ]
            types[type.name] = (type.description, props)
        return types
