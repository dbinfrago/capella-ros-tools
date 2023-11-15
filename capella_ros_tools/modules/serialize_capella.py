# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Class definition for Capella model serializer."""
import typing as t

import capellambse

from . import BASIC_TYPES, ROS_INTERFACES, BaseCapella, MsgProp


class SerializeCapella(BaseCapella):
    """Serializer for Capella model."""

    def __init__(self, path_to_capella_model: str, layer: str) -> None:
        super().__init__(path_to_capella_model, layer)
        self.create_packages({BASIC_TYPES}, self.data)
        self.basic_types = self.data.packages.by_name(BASIC_TYPES)

    def create_packages(self, packages: set[str], package: t.Any) -> None:
        """Create packages in Capella model."""
        for package_name in packages:
            try:
                package.packages.by_name(package_name)
            except KeyError:
                package.packages.create("DataPkg", name=package_name)

    def create_classes(
        self,
        classes: dict[str, tuple[str, list]],
        package: t.Any,
    ) -> list:
        """Create classes in Capella model."""
        overlap = []
        for class_name, info in classes.items():
            try:
                overlap.append(package.classes.by_name(class_name))
            except KeyError:
                description, _ = info
                package.classes.create(
                    name=class_name, description=description
                )
        return overlap

    def delete_classes(self, classes: list, package: t.Any) -> None:
        """Delete classes in Capella model."""
        for cls in classes:
            try:
                package.classes.remove(cls)
            except KeyError:
                pass

    def create_types(
        self, types: dict[str, tuple[str, list]], package: t.Any
    ) -> list:
        """Create types in Capella model."""
        overlap = []
        for type_name, info in types.items():
            try:
                overlap.append(package.datatypes.by_name(type_name))
            except KeyError:
                description, properties = info
                type = package.datatypes.create(
                    "Enumeration", name=type_name, description=description
                )
                for prop in properties:
                    property = type.owned_literals.create(
                        "EnumerationLiteral",
                        name=prop.name,
                        description=prop.comment,
                    )
                    self.create_basic_types({prop.type})
                    property.value = capellambse.new_object(
                        "LiteralNumericValue",
                        value=float(prop.value),
                        type=self.basic_types.datatypes.by_name(prop.type),
                    )
        return overlap

    def delete_types(self, types: list, package: t.Any) -> None:
        """Delete types in Capella model."""
        for type in types:
            try:
                package.datatypes.remove(type)
            except KeyError:
                pass

    def create_basic_types(self, basic_types: set[str]) -> list:
        """Create basic types in Capella model."""
        overlap = []
        for basic_type in basic_types:
            try:
                overlap.append(self.basic_types.datatypes.by_name(basic_type))
            except KeyError:
                if basic_type in ["string", "char"]:
                    type = "StringType"
                elif basic_type == "bool":
                    type = "BooleanType"
                else:
                    type = "NumericType"
                self.basic_types.datatypes.create(type, name=basic_type)
        return overlap

    def create_composition(
        self,
        class_name: str,
        prop: MsgProp,
        package: t.Any,
    ) -> bool:
        """Create composition in Capella model."""
        superclass = package.classes.by_name(class_name)
        try:
            partclass = (
                (
                    self.data.packages.by_name(ROS_INTERFACES)
                    .packages.by_name(prop.typedir)
                    .classes.by_name(prop.type)
                )
                if prop.typedir
                else self.model.search("Class", below=package).by_name(
                    prop.type
                )
            )
        except KeyError:
            return False
        try:
            p = superclass.owned_properties.by_name(prop.name)
            superclass.owned_properties.remove(p)
        except KeyError:
            pass
        composition = superclass.owned_properties.create(
            name=prop.name,
            type=partclass,
            kind="COMPOSITION",
            description=prop.comment,
        )
        association = package.owned_associations.create(
            navigable_members=[composition]
        )
        association.members.create(
            "Property",
            type=superclass,
            kind="ASSOCIATION",
            min_card=capellambse.new_object("LiteralNumericValue", value=1),
            max_card=capellambse.new_object("LiteralNumericValue", value=1),
        )
        composition.min_card = capellambse.new_object(
            "LiteralNumericValue", value=float(prop.min)
        )
        composition.max_card = capellambse.new_object(
            "LiteralNumericValue", value=float(prop.max or "inf")
        )
        return True

    def _find_type(self, type_name: str, package: t.Any) -> t.Any:
        """Find type in Capella model."""
        try:
            return self.model.search("Enumeration", below=package).by_name(
                type_name
            )
        except KeyError:
            pass
        try:
            return self.basic_types.datatypes.by_name(type_name)
        except KeyError:
            return None

    def create_attribute(
        self,
        class_name: str,
        prop: MsgProp,
        package: t.Any,
    ) -> bool:
        """Create attribute in Capella model."""
        superclass = package.classes.by_name(class_name)
        property_type = self._find_type(prop.type, package)
        if not property_type:
            return False
        try:
            p = superclass.owned_properties.by_name(prop.name)
            superclass.owned_properties.remove(p)
        except KeyError:
            pass
        attribute = superclass.owned_properties.create(
            name=prop.name,
            type=property_type,
            kind="COMPOSITION",
            description=prop.comment,
        )
        attribute.min_card = capellambse.new_object(
            "LiteralNumericValue", value=float(prop.min)
        )
        attribute.max_card = capellambse.new_object(
            "LiteralNumericValue", value=float(prop.max or "inf")
        )
        return True

    def save_changes(self) -> None:
        """Save changes to Capella model."""
        self.model.save()
