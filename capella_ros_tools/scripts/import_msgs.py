# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Tool for importing ROS messages to a Capella data package."""

import logging

import click
from capellambse.filehandler import abc
from capellambse.model.crosslayer import information

from capella_ros_tools import capella, messages

ROS2_INTERFACES = {
    "common_interfaces": "git+https://github.com/ros2/common_interfaces",
    "rcl_interfaces": "git+https://github.com/ros2/rcl_interfaces",
    "unique_identifier_msgs": "git+https://github.com"
    "/ros2/unique_identifier_msgs",
}


logger = logging.getLogger(__name__)


class Importer:
    """Class for importing ROS messages to a Capella data package."""

    def __init__(
        self,
        msg_path: abc.AbstractFilePath,
        capella_path: str,
        layer: str,
        action: str,
        no_deps: bool,
    ):
        pkg_name = msg_path.stem if msg_path.stem else "ros_msgs"
        pkg_def = messages.MessagePkgDef.from_msg_folder(pkg_name, msg_path)

        self.messages = messages.MessagePkgDef("", [], [pkg_def])
        self.capella = capella.CapellaDataPackage(capella_path, layer)
        self.action = action

        if no_deps:
            return
        from capellambse import filehandler

        for interface_name, interface_url in ROS2_INTERFACES.items():
            interface_path = filehandler.get_filehandler(interface_url).rootdir
            for dir in interface_path.rglob("msg"):
                pkg_name = dir.parent.name or interface_name
                pkg_def = messages.MessagePkgDef.from_msg_folder(pkg_name, dir)
                self.messages.packages.append(pkg_def)

    def _handle_objects_skip(
        self,
        elem_def_list: list,
        attr_name: str,
        current_root: information.DataPkg,
    ):
        for elem_def in elem_def_list:
            getattr(self.capella, f"create_{attr_name}")(
                elem_def, current_root
            )

    def _handle_objects_replace(
        self,
        elem_def_list: list,
        attr_name: str,
        current_root: information.DataPkg,
    ):
        for elem_def in elem_def_list:
            if elem_obj := getattr(self.capella, f"create_{attr_name}")(
                elem_def, current_root
            ):
                getattr(self.capella, f"remove_{attr_name}")(
                    elem_obj, current_root
                )
                getattr(self.capella, f"create_{attr_name}")(
                    elem_def, current_root
                )

    def _handle_objects_abort(
        self,
        elem_def_list: list,
        attr_name: str,
        current_root: information.DataPkg,
    ):
        for elem_def in elem_def_list:
            if getattr(self.capella, f"create_{attr_name}")(
                elem_def, current_root
            ):
                raise click.Abort()

    def _handle_objects_ask(
        self,
        elem_def_list: list,
        attr_name: str,
        current_root: information.DataPkg,
    ):
        for i, elem_def in enumerate(elem_def_list):
            if elem_obj := getattr(self.capella, f"create_{attr_name}")(
                elem_def, current_root
            ):
                confirm = click.prompt(
                    f"{elem_def.name} already exists. Overwrite? [y]es / [Y]es to all / [n]o / [N]o to all",
                    type=click.Choice(
                        ["y", "Y", "n", "N"],
                        case_sensitive=True,
                    ),
                )
                if confirm == "n":
                    continue
                elif confirm == "N":
                    for elem_def in elem_def_list[(i + 1) :]:
                        getattr(self.capella, f"create_{attr_name}")(
                            elem_def, current_root
                        )
                    self.action = "skip"
                    break
                elif confirm == "y":
                    getattr(self.capella, f"remove_{attr_name}")(
                        elem_obj, current_root
                    )
                    getattr(self.capella, f"create_{attr_name}")(
                        elem_def, current_root
                    )
                elif confirm == "Y":
                    for elem_def in elem_def_list[i:]:
                        if elem_obj := getattr(
                            self.capella, f"create_{attr_name}"
                        )(elem_def, current_root):
                            getattr(self.capella, f"remove_{attr_name}")(
                                elem_obj, current_root
                            )
                            getattr(self.capella, f"create_{attr_name}")(
                                elem_def, current_root
                            )
                    self.action = "replace"
                    break

    def _handle_objects(
        self,
        current_pkg_def: messages.MessagePkgDef,
        current_root: information.DataPkg,
    ):
        elem_types = [
            ("package", current_pkg_def.packages),
            ("class", current_pkg_def.messages),
            (
                "enum",
                [
                    enum
                    for msg in current_pkg_def.messages
                    for enum in msg.enums
                ],
            ),
        ]

        for elem_type, elem_def_list in elem_types:
            getattr(self, f"_handle_objects_{self.action}")(
                elem_def_list, elem_type, current_root
            )

        for new_pkg_def in current_pkg_def.packages:
            new_root = current_root.packages.by_name(new_pkg_def.name)
            self._handle_objects(new_pkg_def, new_root)

    def _handle_relations(
        self,
        current_pkg_def: messages.MessagePkgDef,
        current_root: information.DataPkg,
    ):
        for msg in current_pkg_def.messages:
            self.capella.create_properties(msg, current_root)

        for new_pkg_def in current_pkg_def.packages:
            new_root = current_root.packages.by_name(new_pkg_def.name)
            self._handle_relations(new_pkg_def, new_root)

    def __call__(self):
        """Convert JSON to Capella data package."""
        current_root = self.capella.data_package

        self._handle_objects(self.messages, current_root)
        self._handle_relations(self.messages, current_root)

        self.capella.save_changes()
