# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Convert ROS messages to Capella data.""" ""
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
    "int8": "Short",
    "uint8": "UnsignedShort",
    "int16": "Integer",
    "uint16": "UnsignedInteger",
    "int32": "Long",
    "uint32": "UnsignedLong",
    "int64": "LongLong",
    "uint64": "UnsignedLongLong",
    "float32": "Float",
    "float64": "Double",
    "string": "String",
    "wstring": "Char",
}


class Converter:
    """Converts ROS messages to Capella data."""

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
        if not overlap or self.action == "k":
            return
        if self.action == "a":
            click.echo(
                f"{len(overlap)} elements already exist."
                " Use --exists-action=o to overwrite."
            )
            raise click.Abort()
        elif self.action == "o":
            deletion_func(overlap, current_root)
        elif self.action == "c":
            for i, cls in enumerate(overlap):
                confirm = click.prompt(
                    f"{cls.name} already exists. " "Do you want to overwrite?",
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

        enums = [
            EnumDef(
                e.name,
                [
                    EnumValue(
                        MSG_TYPE_TO_CAPELLA.get(v.type.name) or v.type.name,
                        v.name,
                        int(v.value),
                        "\n".join(v.annotations),
                    )
                    for v in e.values
                ],
                "\n".join(e.annotations),
            )
            for msg in current_pkg_def.messages
            for e in msg.enums
            if e.values
        ]
        overlap = self.model.create_enums(enums, current_root)
        self._resolve_overlap(overlap, self.model.delete_enums, current_root)
        self.model.create_enums(enums, current_root)

        classes = [
            ClassDef(c.name, [], "\n".join(c.annotations))
            for c in current_pkg_def.messages
            if c.fields
        ]
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
            self.model.create_properties(
                ClassDef(
                    name=msg.name,
                    properties=[
                        ClassProperty(
                            MSG_TYPE_TO_CAPELLA.get(f.type.name)
                            or f.type.name,
                            f.type.pkg_name,
                            f.name,
                            min_card=0 if f.type.array_size else 1,
                            max_card=f.type.array_size or 1,
                            description="\n".join(f.annotations),
                        )
                        for f in msg.fields
                    ],
                    description="\n".join(msg.annotations),
                ),
                current_root,
            )

        for new_pkg_def in current_pkg_def.packages:
            new_root = current_root.packages.by_name(new_pkg_def.name)
            self._add_relations(new_pkg_def, new_root)

    def convert(self) -> None:
        """Convert ROS messages to Capella data."""
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
