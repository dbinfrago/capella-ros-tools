# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""IDL model definitions."""
import os
import typing as t

import rosidl2capella.rosidl_parser as parser

PATH = os.path.dirname(__file__)


class IDLPackage:
    """IDL package definition."""

    classes: dict[str, t.Any]
    types: dict[str, t.Any]
    basic_types: set[str]

    def __init__(
        self,
        classes: dict[str, t.Any] | set[str],
        types: dict[str, t.Any] | set[str],
        basic_types: set[str],
    ) -> None:
        self.classes = (
            classes
            if isinstance(classes, dict)
            else {k: None for k in classes}
        )
        self.types = (
            types if isinstance(types, dict) else {k: None for k in types}
        )
        self.basic_types = basic_types


class IDLModel:
    """IDL model definition."""

    packages: dict[str, IDLPackage]

    def __init__(self, packages: dict[str, IDLPackage]) -> None:
        self.packages = packages

    @classmethod
    def from_msg_model(cls, path_to_msg_model: str) -> "IDLModel":
        """Create IDL model from message files."""
        packages = {}
        packages["root"] = cls._parse_package(path_to_msg_model)
        common_msgs_dir = os.path.join(PATH, "ros", "common_msgs")
        for dir_name in os.listdir(common_msgs_dir):
            if os.path.isdir(os.path.join(common_msgs_dir, dir_name)):
                packages[dir_name] = cls._parse_package(
                    os.path.join(common_msgs_dir, dir_name)
                )
        packages["std_msgs"] = cls._parse_package(
            os.path.join(PATH, "ros", "std_msgs")
        )
        return cls(packages)

    @staticmethod
    def _parse_package(path_to_pkg_root: str) -> IDLPackage:
        """Parse package from message files."""
        classes = parser.MessagesPkg.from_msg_folder(
            path_to_pkg_root
        ).as_structs
        types = parser.MessagesPkg.from_msg_folder(
            path_to_pkg_root, True
        ).as_structs
        basic_types = set()
        all_type_defs = classes | types
        for _, properties in all_type_defs.values():
            for prop in properties:
                prop_type = prop[1]
                if prop_type not in all_type_defs:
                    basic_types.add(prop_type)
        return IDLPackage(classes, types, basic_types)

    def delete_from_model(self, to_delete: dict[str, IDLPackage]) -> None:
        """Delete elements from IDL model."""
        for pkg_name, package in to_delete.items():
            for class_name in package.classes.keys():
                self.packages[pkg_name].classes.pop(class_name)
            for type_name in package.types.keys():
                self.packages[pkg_name].types.pop(type_name)
            self.packages[pkg_name].basic_types -= package.basic_types
