# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Convert Capella data to ROS messages."""
import typing as t

from capella_ros_tools.modules.capella.parser import CapellaModel
from capella_ros_tools.modules.messages import (
    BaseTypeDef,
    ConstantDef,
    EnumDef,
    FieldDef,
)
from capella_ros_tools.modules.messages.serializer import (
    MessageDef,
    MessagePkgDef,
)

CAPELLA_TYPE_TO_MSG = {
    "Boolean": "bool",
    "Byte": "byte",
    "Char": "char",
    "Short": "int8",
    "UnsignedShort": "uint8",
    "Integer": "int16",
    "UnsignedInteger": "uint16",
    "Long": "int32",
    "UnsignedLong": "uint32",
    "LongLong": "int64",
    "UnsignedLongLong": "uint64",
    "Float": "float32",
    "Double": "float64",
    "String": "string",
}


class Converter:
    """Converter class for converting Capella data to ROS messages."""

    def __init__(
        self,
        msg_path: t.Any,
        capella_path: t.Any,
        layer: str,
        action: str,
        no_deps: bool,
    ) -> None:
        self.msg_path = msg_path
        self.msgs = MessagePkgDef(msg_path.stem, [], [])
        self.model = CapellaModel(capella_path, layer)
        self.action = action
        self.no_deps = no_deps

    def _add_package(self, current_root: t.Any) -> MessagePkgDef:
        current_pkg_def = MessagePkgDef(current_root.name, [], [])

        for cls in self.model.get_classes(current_root):
            current_pkg_def.messages.append(
                MessageDef(
                    cls.name,
                    [
                        FieldDef(
                            BaseTypeDef(
                                CAPELLA_TYPE_TO_MSG[prop.type_name]
                                if prop.type_name in CAPELLA_TYPE_TO_MSG
                                else prop.type_name,
                                None
                                if prop.max_card == "1"
                                else prop.max_card,
                                None
                                if prop.type_pkg_name == current_pkg_def.name
                                else prop.type_pkg_name,
                            ),
                            prop.name,
                            prop.description.split("\n"),
                        )
                        for prop in cls.properties
                    ],
                    [],
                    cls.description.split("\n"),
                )
            )

        for enum in self.model.get_enums(current_root):
            current_pkg_def.messages.append(
                MessageDef(
                    enum.name,
                    [],
                    [
                        EnumDef(
                            enum.name,
                            [
                                ConstantDef(
                                    BaseTypeDef(
                                        CAPELLA_TYPE_TO_MSG.get(value.type)
                                        or "uint8"
                                    ),
                                    value.name,
                                    value.value or str(i),
                                    value.description.split("\n"),
                                )
                                for i, value in enumerate(enum.values)
                            ],
                            [],
                        )
                    ],
                    enum.description.split("\n"),
                )
            )

        for pkg_name in self.model.get_packages(current_root):
            new_root = current_root.packages.by_name(pkg_name)
            current_pkg_def.packages.append(self._add_package(new_root))

        return current_pkg_def

    def convert(self) -> None:
        """Start conversion."""
        self.msgs.packages.append(self._add_package(self.model.data))
        self.msgs.to_msg_folder(self.msg_path)
