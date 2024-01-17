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
    "Short": "int16",
    "UnsignedShort": "uint16",
    "Integer": "int32",
    "UnsignedInteger": "uint32",
    "Long": "int64",
    "UnsignedLong": "uint64",
    "LongLong": "int128",
    "UnsignedLongLong": "uint128",
    "Float": "float32",
    "Double": "float64",
    "LongDouble": "float128",
    "String": "string",
}


class Converter:
    """Converter class for converting Capella data to ROS messages."""

    def __init__(
        self,
        msg_path: t.Any,
        capella_path: t.Any,
        layer: str,
    ) -> None:
        self.msg_path = msg_path
        self.msgs = MessagePkgDef(msg_path.stem, [], [])
        self.model = CapellaModel(capella_path, layer)

    def _add_package(self, current_root: t.Any) -> MessagePkgDef:
        current_pkg_def = MessagePkgDef(current_root.name, [], [])

        for cls in self.model.get_classes(current_root):
            fields = []
            for prop in cls.properties:
                bt_name = CAPELLA_TYPE_TO_MSG.get(
                    prop.type_name, prop.type_name
                )
                bt_size = None if prop.max_card == "1" else prop.max_card
                if prop.type_pkg_name != current_pkg_def.name:
                    bt_pkg = prop.type_pkg_name
                else:
                    bt_pkg = None
                fields.append(
                    FieldDef(
                        BaseTypeDef(bt_name, bt_size, bt_pkg),
                        prop.name,
                        prop.description.split("\n"),
                    )
                )
            annotations = cls.description.split("\n")
            msg_def = MessageDef(cls.name, fields, [], annotations)
            current_pkg_def.messages.append(msg_def)

        for enum in self.model.get_enums(current_root):
            values = []
            for i, value in enumerate(enum.values):
                bt_name = CAPELLA_TYPE_TO_MSG.get(value.type, "uint8")
                values.append(
                    ConstantDef(
                        BaseTypeDef(bt_name),
                        value.name,
                        value.value or str(i),
                        value.description.split("\n"),
                    )
                )
            enum_def = EnumDef(enum.name, values, [])
            annotations = enum.description.split("\n")
            msg_def = MessageDef(enum.name, [], [enum_def], annotations)
            current_pkg_def.messages.append(msg_def)

        for pkg_name in self.model.get_packages(current_root):
            new_root = current_root.packages.by_name(pkg_name)
            current_pkg_def.packages.append(self._add_package(new_root))

        return current_pkg_def

    def convert(self) -> None:
        """Start conversion."""
        self.msgs.packages.append(self._add_package(self.model.data))
        self.msgs.to_msg_folder(self.msg_path)
