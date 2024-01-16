# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Import ROS messages into Capella."""
import typing as t

import capellambse
import click

from capella_ros_tools.modules.capella import (
    ClassDef,
    ClassProperty,
    EnumDef,
    EnumValue,
)
from capella_ros_tools.modules.capella.serializer import CapellaModel
from capella_ros_tools.modules.messages.parser import MessagePkgDef

ROS2_INTERFACES = {
    "common_interfaces": "git+https://github.com/ros2/common_interfaces",
    "rcl_interfaces": "git+https://github.com/ros2/rcl_interfaces",
    "unique_identifier_msgs": "git+https://github.com"
    "/ros2/unique_identifier_msgs",
}

MSG_TYPE_TO_CAPELLA = {
    "bool": "Boolean",
    "byte": "Byte",
    "char": "Char",
    "string": "String",
}


class Converter:
    """Converter class for importing ROS messages into Capella."""

    def __init__(
        self,
        msg_path: t.Any,
        capella_path: t.Any,
        layer: str,
        action: str,
        no_deps: bool,
    ) -> None:
        self.msgs = MessagePkgDef.from_pkg_folder(msg_path)
        self.model = CapellaModel(capella_path, layer)
        self.action = action
        self.no_deps = no_deps

    def _resolve_overlap(self, overlap, deletion_func, current_root):
        if not overlap or self.action == "skip":
            return
        if self.action == "abort":
            click.echo(
                f"{len(overlap)} elements already exist."
                " Use --exists-action=replace to replace."
            )
            raise click.Abort()
        elif self.action == "replace":
            deletion_func(overlap, current_root)
        elif self.action == "ask":
            for i, cls in enumerate(overlap):
                confirm = click.prompt(
                    f"{cls.name} already exists. Overwrite? [y]es / [Y]es to all / [n]o / [N]o to all",
                    type=click.Choice(
                        ["y", "Y", "n", "N"],
                        case_sensitive=True,
                    ),
                )
                if confirm == "n":
                    continue
                elif confirm == "N":
                    self.action = "k"
                    return
                elif confirm == "Y":
                    deletion_func(overlap[i:], current_root)
                    self.action = "o"
                    return
                elif confirm == "y":
                    deletion_func([cls], current_root)

    def _add_objects(
        self, current_pkg_def: MessagePkgDef, current_root: t.Any
    ):
        packages = [p.name for p in current_pkg_def.packages]
        self.model.create_packages(packages, current_root)

        classes = []
        enums = []
        for msg in current_pkg_def.messages:
            if msg.fields:
                class_description = "\n".join(msg.annotations)
                class_def = ClassDef(
                    msg.name,
                    [],
                    class_description,
                )
                classes.append(class_def)

            for enum in msg.enums:
                if not enum.values:
                    continue
                values = []
                for value in enum.values:
                    value_type = MSG_TYPE_TO_CAPELLA.get(
                        value.type.name, value.type.name
                    )
                    value_description = "\n".join(value.annotations)
                    value_def = EnumValue(
                        value_type,
                        value.name,
                        value.value,
                        value_description,
                    )
                    values.append(value_def)
                enum_description = "\n".join(enum.annotations)
                enum_def = EnumDef(
                    enum.name,
                    values,
                    enum_description,
                )
                enums.append(enum_def)

        overlap = self.model.create_enums(enums, current_root)
        self._resolve_overlap(overlap, self.model.delete_enums, current_root)
        self.model.create_enums(enums, current_root)

        overlap = self.model.create_classes(classes, current_root)
        self._resolve_overlap(overlap, self.model.delete_classes, current_root)
        self.model.create_classes(classes, current_root)

        for new_pkg_def in current_pkg_def.packages:
            new_root = current_root.packages.by_name(new_pkg_def.name)
            self._add_objects(new_pkg_def, new_root)

    def _add_relations(self, current_pkg_def, current_root):
        for msg in current_pkg_def.messages:
            if not msg.fields:
                continue
            properties = []
            for field in msg.fields:
                field_type = MSG_TYPE_TO_CAPELLA.get(
                    field.type.name, field.type.name
                )
                field_min = "0" if field.type.array_size else "1"
                field_max = field.type.array_size or "1"
                field_description = "\n".join(field.annotations)
                property_def = ClassProperty(
                    field_type,
                    field.type.pkg_name,
                    field.name,
                    field_min,
                    field_max,
                    field_description,
                )
                properties.append(property_def)
            class_def = ClassDef(
                msg.name,
                properties,
                "",
            )
            self.model.create_properties(class_def, current_root)

        for new_pkg_def in current_pkg_def.packages:
            new_root = current_root.packages.by_name(new_pkg_def.name)
            self._add_relations(new_pkg_def, new_root)

    def convert(self) -> None:
        """Start conversion."""
        current_root = self.model.data

        if not self.no_deps:
            imported_ros2_packages = []
            for interface_name, interface_url in ROS2_INTERFACES.items():
                interface_path = capellambse.filehandler.get_filehandler(
                    interface_url
                ).rootdir
                interface_pkg_def = MessagePkgDef.from_pkg_folder(
                    interface_path, interface_name
                )
                interface_pkg_def.name = (
                    interface_pkg_def.name or interface_name
                )
                imported_ros2_packages.append(interface_pkg_def)
                self._add_objects(interface_pkg_def, current_root)

            for interface_pkg_def in imported_ros2_packages:
                self._add_relations(interface_pkg_def, current_root)

        self._add_objects(self.msgs, current_root)
        self._add_relations(self.msgs, current_root)

        self.model.save_changes()
