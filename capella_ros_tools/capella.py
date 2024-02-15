# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""High-level interface for interacting with Capella data packages."""

import logging
import typing as t

import capellambse
from capellambse.model.crosslayer import information

from capella_ros_tools import messages

logger = logging.getLogger(__name__)


class CapellaDataPackage:
    """Capella data package wrapper."""

    def __init__(self, capella_path: str, layer: str):
        self.model = capellambse.MelodyModel(capella_path)
        self.data_package = getattr(self.model, layer).data_package
        try:
            self.data_types = self.model.sa.data_package.packages.by_name(
                "Data Types"
            )
        except KeyError:
            self.data_types = self.model.sa.data_package.packages.create(
                name="Data Types"
            )

    def remove_class(
        self, cls_obj: information.Class, remove_from: information.DataPkg
    ):
        """Remove class from Capella package."""
        try:
            remove_from.classes.remove(cls_obj)
            logger.info("%s deleted.", cls_obj._short_repr_())
        except ValueError:
            pass

    def remove_package(
        self, pkg_obj: information.DataPkg, remove_from: information.DataPkg
    ):
        """Remove package from Capella package."""
        try:
            remove_from.packages.remove(pkg_obj)
            logger.info("%s deleted.", pkg_obj._short_repr_())
        except ValueError:
            pass

    def remove_enum(
        self,
        enum_obj: information.datatype.Enumeration,
        remove_from: information.DataPkg,
    ):
        """Remove enum from Capella package."""
        try:
            remove_from.datatypes.remove(enum_obj)
            logger.info("%s deleted.", enum_obj._short_repr_())
        except ValueError:
            pass

    def create_package(
        self,
        pkg_def: messages.MessagePkgDef,
        create_in: information.DataPkg,
    ) -> information.DataPkg | None:
        """Create package in Capella package.

        Returns
        -------
            Package object if package already exists, else None.
        """
        try:
            pkg_obj = self.model.search(
                "DataPkg", below=self.data_package
            ).by_name(pkg_def.name)
            logger.info("%s already exists.", pkg_obj._short_repr_())
            return pkg_obj
        except KeyError:
            pkg_obj = create_in.packages.create(
                name=pkg_def.name,
            )
            logger.info("%s created.", pkg_obj._short_repr_())
            return None

    def create_class(
        self,
        cls_def: messages.MessageDef,
        create_in: information.DataPkg,
    ) -> information.Class | None:
        """Create class in Capella package.

        Returns
        -------
            Class object if class already exists, else None.
        """
        try:
            cls_obj = create_in.classes.by_name(cls_def.name)
            logger.info("%s already exists.", cls_obj._short_repr_())
            return cls_obj
        except KeyError:
            cls_obj = create_in.classes.create(
                name=cls_def.name, description=cls_def.description
            )
            logger.info("%s created.", cls_obj._short_repr_())
            return None

    def create_enum(
        self, enum_def: messages.EnumDef, create_in: information.DataPkg
    ) -> information.datatype.Enumeration | None:
        """Create enum in Capella package.

        Returns
        -------
            Enumeration object if enumeration already exists, else None.
        """
        try:
            enum_obj = create_in.datatypes.by_name(enum_def.name)
            logger.info("%s already exists.", enum_obj._short_repr_())
            return enum_obj
        except KeyError:
            enum_obj = create_in.datatypes.create(
                "Enumeration",
                name=enum_def.name,
                description=enum_def.description,
            )
            for literal in enum_def.literals:
                literal_obj = enum_obj.owned_literals.create(
                    "EnumerationLiteral",
                    name=literal.name,
                    description=literal.description,
                )
                literal_obj.value = capellambse.new_object(
                    "LiteralNumericValue",
                    value=str(literal.value),
                )
            logger.info("%s created.", enum_obj._short_repr_())
            return None

    def _get_parent(
        self, package_name: str | None, default: information.DataPkg
    ) -> information.DataPkg:
        try:
            return self.model.search(
                "DataPkg", below=self.data_package
            ).by_name(package_name)
        except KeyError:
            return default

    def create_properties(
        self,
        cls_def: messages.MessageDef,
        create_in: information.DataPkg,
    ) -> None:
        """Create properties for Capella class."""
        superclass = create_in.classes.by_name(cls_def.name)

        for prop in cls_def.fields:
            try:
                parent = self._get_parent(prop.type.package, create_in)
                partclass = parent.classes.by_name(prop.type.name)
                composition = self._create_composition(
                    superclass, prop, partclass
                )
                association = create_in.owned_associations.create(
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
            except KeyError:
                composition = self._create_attribute(
                    superclass, prop, create_in
                )

            self._set_cardinality(composition, prop.type.card)
            self._set_range(composition, prop.type.range)
        logger.info("Created properties for %s.", cls_def.name)

    def _create_attribute(
        self,
        superclass: information.Class,
        attr: messages.FieldDef,
        parent: information.DataPkg,
    ) -> information.Property:
        type_name = attr.type.name
        try:
            attr_type = parent.datatypes.by_name(type_name)
        except KeyError:
            if "char" in type_name or "string" in type_name:
                type = "StringType"
            elif "bool" in type_name or "boolean" in type_name:
                type = "BooleanType"
            else:
                type = "NumericType"

            attr_type = self.data_types.datatypes.create(type, name=type_name)

        composition = self._create_composition(superclass, attr, attr_type)
        return composition

    def _create_composition(
        self,
        superclass: information.Class,
        prop_def: messages.FieldDef,
        property_type: (
            information.Class | t.Type[information.datatype.DataType]
        ),
    ) -> information.Property:
        """Create composition for Capella class."""
        try:
            overlap = superclass.owned_properties.by_name(prop_def.name)
            superclass.owned_properties.remove(overlap)
        except KeyError:
            pass
        composition = superclass.owned_properties.create(
            name=prop_def.name,
            type=property_type,
            kind="COMPOSITION",
            description=prop_def.description,
        )
        return composition

    def _set_cardinality(
        self, composition: information.Property, card: messages.Range
    ) -> None:
        """Set cardinality for composition in Capella model."""
        composition.min_card = capellambse.new_object(
            "LiteralNumericValue", value=card.min
        )
        composition.max_card = capellambse.new_object(
            "LiteralNumericValue", value=card.max
        )

    def _set_range(
        self, composition: information.Property, range: messages.Range | None
    ) -> None:
        """Set range for composition in Capella model."""
        if range:
            composition.min = capellambse.new_object(
                "LiteralNumericValue", value=range.min
            )
            composition.max = capellambse.new_object(
                "LiteralNumericValue", value=range.max
            )

    def save_changes(self) -> None:
        """Save changes to Capella model."""
        self.model.save()
