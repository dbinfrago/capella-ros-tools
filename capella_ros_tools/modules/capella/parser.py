# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Parser for Capella model."""
import typing as t

from . import BaseCapellaModel, ClassDef, ClassProperty, EnumDef, EnumValue


class CapellaModel(BaseCapellaModel):
    """Capella model definition for parsing model."""

    def get_packages(self, package: t.Any) -> set[str]:
        """Get packages in Capella model."""
        return {pkg.name for pkg in package.packages}

    def get_classes(self, package: t.Any) -> list[ClassDef]:
        """Get classes in Capella model."""
        classes = []
        for cls in package.classes:
            props = []
            for prop in cls.owned_properties:
                type: t.Any
                if prop.type.__class__.__name__ == "Enumeration":
                    type = EnumDef(
                        prop.type.name,
                        [
                            EnumValue(
                                literal.value.type.name,
                                literal.name,
                                literal.value.value,
                                literal.description,
                            )
                            for literal in prop.type.owned_literals
                        ],
                        prop.type.description,
                    )
                elif prop.type.__class__.__name__ == "Class":
                    type = ClassDef(
                        prop.type.name,
                        [],
                        prop.type.description,
                    )
                else:
                    type = prop.type.name

                type_pkg_name = prop.type.parent.name
                if type_pkg_name in [
                    "Predefined Types",
                    cls.parent.name,
                ]:
                    type_pkg_name = None

                props.append(
                    ClassProperty(
                        prop.name,
                        type,
                        type_pkg_name,
                        prop.min_card.value,
                        prop.max_card.value,
                        prop.description,
                    )
                )
            classes.append(
                ClassDef(
                    cls.name,
                    props,
                    cls.description,
                )
            )
        return classes
