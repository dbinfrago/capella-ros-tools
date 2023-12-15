# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Convert Capella data to ROS messages."""
import typing as t

from capella_ros_tools.modules.capella.parser import CapellaModel

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
    """Convert Capella data to ROS messages."""

    def __init__(self, capella_path: t.Any, layer: str, merge: str) -> None:
        self.model = CapellaModel(capella_path, layer)
        self.merge = merge

    def convert(self) -> None:
        """Convert Capella data to ROS messages."""
        return
