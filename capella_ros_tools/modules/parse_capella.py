# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Class definition for Capella model parser."""
import typing as t

from . import ROS_INTERFACES, BaseCapella, EnumProp, MsgProp


class ParseCapella(BaseCapella):
    """Parser for Capella model."""

    def get_packages(self, package: t.Any) -> set[str]:
        """Get packages in Capella model."""
        return {pkg.name for pkg in package.packages}

    def get_classes(self, package: t.Any) -> dict[str, t.Any]:
        """Get classes in Capella model."""
        classes: dict = {}
        for cls in package.classes:
            props = []
            for prop in cls.owned_properties:
                type = (
                    prop.type.name
                    if prop.type.__class__.__name__ != "Enumeration"
                    else "uint8"
                )
                typedir = (
                    prop.type.parent.name
                    if prop.type.parent.parent.name == ROS_INTERFACES
                    else ""
                )
                props.append(
                    MsgProp(
                        prop.name,
                        type,
                        typedir,
                        prop.min_card.value,
                        prop.max_card.value,
                        prop.description,
                    )
                )
            classes[cls.name] = (cls.description, props)
        return classes

    def get_types(self, package: t.Any) -> dict[str, t.Any]:
        """Get types in Capella model."""
        types: dict = {}
        for type in package.datatypes:
            props = [
                EnumProp(
                    prop.name,
                    prop.value.type.name if prop.value.type else "uint8",
                    prop.value.value,
                    prop.description,
                )
                for prop in type.owned_literals
            ]
            types[type.name] = (type.description, props)
        return types
