# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Serializer for Capella model."""
import logging
import typing as t

import capellambse

from . import BaseCapellaModel, ClassDef, ClassProperty, EnumDef

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CapellaModel(BaseCapellaModel):
    """Capella model definition for serialized model."""

    def create_packages(
        self, packages: list[str], package: t.Any = None
    ) -> None:
        """Create packages in Capella model."""

        if package is None:
            package = self.data

        for package_name in packages:
            try:
                package.packages.by_name(package_name)
            except KeyError:
                package.packages.create("DataPkg", name=package_name)
                logger.info("Created package %s.", package_name)

    def create_classes(
        self,
        classes: list[ClassDef],
        package: t.Any = None,
    ) -> list:
        """Create classes in Capella model."""
        if package is None:
            package = self.data

        overlap = []
        for cls in classes:
            try:
                overlap.append(
                    self.model.search("Class", below=package).by_name(cls.name)
                )
                logger.info("Class %s already exists.", cls.name)
            except KeyError:
                package.classes.create(
                    name=cls.name, description=cls.description
                )
                logger.info("Created class %s.", cls.name)
        return overlap

    def delete_classes(self, classes: list, package: t.Any = None) -> None:
        """Delete classes in Capella model."""
        if package is None:
            package = self.data

        for cls in classes:
            try:
                package.classes.remove(cls)
                logger.info("Deleted %s.", cls.name)
            except ValueError:
                pass

    def _find_or_create_type(self, type_name: str, package: t.Any) -> t.Any:
        """Find type in Capella model."""
        try:
            return self.predef_types.by_name(type_name)
        except KeyError:
            pass
        try:
            return package.datatypes.by_name(type_name)
        except KeyError:
            type_name_lower = type_name.lower()
            if "char" in type_name_lower or "string" in type_name_lower:
                type = "StringType"
            elif "bool" in type_name_lower or "boolean" in type_name_lower:
                type = "BooleanType"
            else:
                type = "NumericType"
            package.datatypes.create(type, name=type_name)
            return package.datatypes.by_name(type_name)

    def create_enums(
        self, enums: list[EnumDef], package: t.Any = None
    ) -> list:
        """Create enums in Capella model."""
        if package is None:
            package = self.data

        overlap = []
        for enum in enums:
            try:
                overlap.append(
                    self.model.search("Enumeration", below=package).by_name(
                        enum.name
                    )
                )
                logger.info("Enum %s already exists.", enum.name)
            except KeyError:
                type = package.datatypes.create(
                    "Enumeration", name=enum.name, description=enum.description
                )
                for prop in enum.values:
                    property = type.owned_literals.create(
                        "EnumerationLiteral",
                        name=prop.name,
                        description=prop.description,
                    )
                    property.value = capellambse.new_object(
                        "LiteralNumericValue",
                        value=prop.value,
                        type=self._find_or_create_type(prop.type, package),
                    )
                logger.info("Created enum %s.", enum.name)

        return overlap

    def delete_enums(self, enums: list, package: t.Any = None) -> None:
        """Delete enums in Capella model."""
        if package is None:
            package = self.data

        for enum in enums:
            try:
                package.datatypes.remove(enum)
                logger.info("Deleted %s.", enum.name)
            except ValueError:
                pass

    def create_properties(self, cls: ClassDef, package: t.Any):
        """Create properties for class in Capella model."""
        if package is None:
            package = self.data

        superclass = package.classes.by_name(cls.name)

        for prop in cls.properties:
            try:
                type_package = self.data.packages.by_name(prop.type_pkg_name)
            except KeyError:
                type_package = package

            try:
                partclass = self.model.search(
                    "Class", below=type_package
                ).by_name(prop.type_name)
                if superclass == partclass:
                    raise KeyError
                composition = self._create_composition(
                    superclass, prop, partclass
                )
                association = package.owned_associations.create(
                    navigable_members=[composition]
                )
                association.members.create(
                    "Property",
                    type=superclass,
                    kind="ASSOCIATION",
                    min_card=capellambse.new_object(
                        "LiteralNumericValue", value="1"
                    ),
                    max_card=capellambse.new_object(
                        "LiteralNumericValue", value="1"
                    ),
                )
                self._set_cardinality(composition, prop)
                continue
            except KeyError:
                pass

            try:
                type_package = package.parent.packages.by_name("types")
            except KeyError:
                type_package = package
            try:
                property_type = self.model.search(
                    "Enumeration", below=type_package
                ).by_name(prop.type_name)
            except KeyError:
                property_type = self._find_or_create_type(
                    prop.type_name, package
                )

            attribute = self._create_composition(
                superclass, prop, property_type
            )
            self._set_cardinality(attribute, prop)
        logger.info("Created properties for %s.", cls.name)

    def _create_composition(
        self, superclass: t.Any, prop: ClassProperty, property_type: t.Any
    ):
        """Create composition in Capella model."""
        try:
            overlap = superclass.owned_properties.by_name(prop.name)
            superclass.owned_properties.remove(overlap)
        except KeyError:
            pass
        composition = superclass.owned_properties.create(
            name=prop.name,
            type=property_type,
            kind="COMPOSITION",
            description=prop.description,
        )
        return composition

    def _set_cardinality(self, composition: t.Any, prop: ClassProperty):
        """Set cardinality for composition in Capella model."""
        composition.min_card = capellambse.new_object(
            "LiteralNumericValue", value=prop.min_card
        )
        composition.max_card = capellambse.new_object(
            "LiteralNumericValue", value=prop.max_card
        )

    def save_changes(self) -> None:
        """Save changes to Capella model."""
        self.model.save()
