# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Wrapper for Capella model."""
import capellambse

from rosidl2capella.idl_model import IDLModel, IDLPackage


class CapellaWrapper:
    """Wrapper for Capella model."""

    def __init__(
        self,
        path_to_capella_model: str,
        layer: str,
    ) -> None:
        self.model = capellambse.MelodyModel(path_to_capella_model)
        match layer:
            case "oa":
                self.data = self.model.oa.data_package
            case "sa":
                self.data = self.model.sa.data_package
            case "la":
                self.data = self.model.la.data_package
            case "pa":
                self.data = self.model.pa.data_package

    def create_packages(self, packages: set[str]) -> None:
        """Create packages in Capella model."""
        for package_name in packages:
            try:
                self.data.packages.by_name(package_name)
            except KeyError:
                self.data.packages.create("DataPkg", name=package_name)

    def create_classes(
        self,
        classes: dict[str, tuple[str, list]],
        package_name: str,
    ):
        """Create classes in Capella model."""
        package = self.data.packages.by_name(package_name)
        for class_name, info in classes.items():
            description, _ = info
            package.classes.create(name=class_name, description=description)

    def create_types(
        self, types: dict[str, tuple[str, list]], package_name: str
    ):
        """Create types in Capella model."""
        package = self.data.packages.by_name(package_name)
        for type_name, info in types.items():
            description, properties = info
            type = package.datatypes.create(
                "Enumeration", name=type_name, description=description
            )
            for prop in properties:
                prop_name, _, value, description = prop
                property = type.owned_literals.create(
                    "EnumerationLiteral",
                    name=prop_name,
                    description=description,
                )
                property.value = capellambse.new_object(
                    "LiteralNumericValue", value=float(value)
                )

    def create_basic_types(self, basic_types: set[str], package_name: str):
        """Create basic types in Capella model."""
        package = self.data.packages.by_name(package_name)
        for basic_type in basic_types:
            if basic_type in ["string", "char"]:
                type = "StringType"
            elif basic_type == "bool":
                type = "BooleanType"
            else:
                type = "NumericType"
            package.datatypes.create(type, name=basic_type)

    def create_composition(
        self,
        class_name: str,
        properties: tuple[str, str, str, str, str, str],
        package_name: str,
    ):
        """Create composition in Capella model."""
        (
            prop_name,
            prop_type,
            type_pkg,
            min_card,
            max_card,
            comment,
        ) = properties
        package = self.data.packages.by_name(package_name)
        superclass = package.classes.by_name(class_name)
        type_pkg = type_pkg or package_name
        partclass = self.data.packages.by_name(type_pkg).classes.by_name(
            prop_type
        )
        composition = superclass.owned_properties.create(
            name=prop_name, type=partclass, kind="COMPOSITION"
        )
        association = package.owned_associations.create(
            navigable_members=[composition], description=comment
        )
        association.members.create(
            "Property",
            type=superclass,
            kind="ASSOCIATION",
            min_card=capellambse.new_object("LiteralNumericValue", value=1),
            max_card=capellambse.new_object("LiteralNumericValue", value=1),
        )
        composition.min_card = capellambse.new_object(
            "LiteralNumericValue", value=float(min_card)
        )
        composition.max_card = capellambse.new_object(
            "LiteralNumericValue", value=float(max_card or "inf")
        )

    def create_attribute(
        self,
        class_name: str,
        properties: tuple[str, str, str, str, str, str],
        package_name: str,
    ):
        """Create attribute in Capella model."""
        (
            prop_name,
            prop_type,
            type_pkg,
            min_card,
            max_card,
            comment,
        ) = properties
        package = self.data.packages.by_name(package_name)
        superclass = package.classes.by_name(class_name)
        type_pkg = type_pkg or package_name
        property_type = self.data.packages.by_name(type_pkg).datatypes.by_name(
            prop_type
        )
        attribute = superclass.owned_properties.create(
            name=prop_name,
            type=property_type,
            kind="COMPOSITION",
            description=comment,
        )
        attribute.min_card = capellambse.new_object(
            "LiteralNumericValue", value=float(min_card)
        )
        attribute.max_card = capellambse.new_object(
            "LiteralNumericValue", value=float(max_card or "inf")
        )

    def save_changes(self):
        """Save changes to Capella model."""
        self.model.save()

    def delete_from_capella_model(
        self, to_delete: dict[str, IDLPackage]
    ) -> None:
        """Delete elements from Capella model."""
        for pkg_name, idlpackage in to_delete.items():
            package = self.data.packages.by_name(pkg_name)
            for class_name in idlpackage.classes:
                package.classes.remove(package.classes.by_name(class_name))
            for type_name in idlpackage.types.keys() | idlpackage.basic_types:
                package.datatypes.remove(package.datatypes.by_name(type_name))

    @property
    def as_idlmodel(self) -> IDLModel:
        """Return Capella model as IDL model."""
        packages = {}
        for package in self.data.packages:
            classes = {cls.name: None for cls in package.classes}
            types = {}
            basic_types = set()
            for type in package.datatypes:
                if type.xtype.rpartition(":")[2] == "Enumeration":
                    types[type.name] = None
                else:
                    basic_types.add(type.name)
            packages[package.name] = IDLPackage(
                classes=classes, types=types, basic_types=basic_types
            )
        return IDLModel(packages)
