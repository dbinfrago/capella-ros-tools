# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""CLI for importing .msg to capella model."""
import sys
from pathlib import Path

import click

import capella_ros_tools
from capella_ros_tools.modules import BASIC_TYPES, ROS_INTERFACES
from capella_ros_tools.modules.parse_capella import ParseCapella
from capella_ros_tools.modules.serialize_message import (
    SerializeMessageDef,
    SerializeMessagesPkg,
)


class Capella2Msg:
    """Class for converting capella model to .msg files."""

    def __init__(self, path_to_capella_model, layer, overlap) -> None:
        self.parser = ParseCapella(path_to_capella_model, layer)
        self.overlap = overlap

    def add_package(self, current_root):
        """Add package to message package."""
        out = SerializeMessagesPkg({}, {})

        messages = self.parser.get_classes(current_root)
        types = self.parser.get_types(current_root)

        out.messages = {
            msg_name: SerializeMessageDef(msg_name, desc, props)
            for msg_name, (desc, props) in (messages | types).items()
        }
        out.packages = {
            pkg_name: self.add_package(current_root.packages.by_name(pkg_name))
            for pkg_name in self.parser.get_packages(current_root)
        }
        return out


@click.command()
@click.version_option(
    version=capella_ros_tools.__version__,
    prog_name="capella-ros-tools",
    message="%(prog)s %(version)s",
)
@click.argument(
    "path-to-msgs-root",
    type=click.Path(
        file_okay=False,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
    required=True,
)
@click.argument(
    "path-to-capella-model",
    type=click.Path(
        exists=True,
        readable=True,
        resolve_path=True,
        path_type=str,
    ),
    required=True,
)
@click.argument(
    "layer",
    type=click.Choice(["oa", "sa", "la", "pa"], case_sensitive=False),
    required=True,
)
@click.option(
    "-o",
    "--overlap",
    type=click.Choice(
        ["keep", "overwrite", "ask", "abort"], case_sensitive=False
    ),
    default="ask" if sys.stdin.isatty() else "abort",
)
@click.option("--debug", is_flag=True)
def capella2msg(
    path_to_msgs_root, path_to_capella_model, layer, overlap, debug
):
    """Convert capella model to .msg files."""
    converter = Capella2Msg(path_to_capella_model, layer, overlap)
    current_root = converter.parser.data

    messages = converter.parser.get_classes(current_root)
    types = converter.parser.get_types(current_root)

    packages = converter.parser.get_packages(current_root)
    packages.discard(BASIC_TYPES)
    packages.discard(ROS_INTERFACES)

    root = SerializeMessagesPkg({}, {})
    root.messages = {
        msg_name: SerializeMessageDef(msg_name, desc, props)
        for msg_name, (desc, props) in (messages | types).items()
    }

    root.packages = {
        pkg_name: converter.add_package(
            current_root.packages.by_name(pkg_name)
        )
        for pkg_name in packages
    }

    if debug:
        click.echo(root)
    else:
        root.to_msg_folder(path_to_msgs_root)
