# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""CLI for importing .msg to capella model."""
import sys
from pathlib import Path

import click

import capella_ros_tools
from capella_ros_tools.modules import ROS_INTERFACES
from capella_ros_tools.modules.parse_message import ParseMessagesPkg
from capella_ros_tools.modules.serialize_capella import SerializeCapella

PATH = Path(__file__).parent


class Msg2Capella:
    """Class for importing .msg to capella model."""

    def __init__(self, path_to_capella_model, layer, overlap):
        self.serializer = SerializeCapella(path_to_capella_model, layer)
        self.overlap = overlap

    def add_objects(self, current_root_struct, current_root):
        """Add objects to capella model."""
        messages = current_root_struct.messages
        packages = current_root_struct.packages

        self.serializer.create_packages(set(packages.keys()), current_root)

        func = (
            (self.serializer.create_types, self.serializer.delete_types)
            if current_root.name == "types"
            else (
                self.serializer.create_classes,
                self.serializer.delete_classes,
            )
        )

        overlap = func[0](
            {msg_name: msg.as_struct for msg_name, msg in messages.items()},
            current_root,
        )

        if overlap and self.overlap == "abort":
            click.echo(
                "Items already exist. Use --overlap=overwrite to overwrite."
            )
            raise click.Abort()
        for cls in overlap:
            if self.overlap in ["ask", "overwrite"]:
                if self.overlap == "ask":
                    confirm = click.prompt(
                        f"{cls.name} already exists. Do you want to overwrite?",
                        type=click.Choice(
                            ["y", "Y", "n", "N"],
                            case_sensitive=True,
                        ),
                    )
                    match confirm:
                        case "n":
                            continue
                        case "N":
                            self.overlap = "keep"
                        case "Y":
                            self.overlap = "overwrite"

                func[1]([cls], current_root)
                func[0]({cls.name: messages[cls.name].as_struct}, current_root)

        for pkg_name, pkg in packages.items():
            new_root = current_root.packages.by_name(pkg_name)
            self.add_objects(pkg, new_root)

    def add_relations(self, current_root_struct, current_root):
        """Add relations to capella model."""
        messages = current_root_struct.messages
        packages = current_root_struct.packages

        if current_root.name == "types":
            return
        for class_name, cls in messages.items():
            for prop in cls.props:
                if not self.serializer.create_composition(
                    class_name, prop, current_root
                ):
                    self.serializer.create_attribute(
                        class_name, prop, current_root
                    )
        for pkg_name, pkg in packages.items():
            new_root = current_root.packages.by_name(pkg_name)
            self.add_relations(pkg, new_root)


@click.command()
@click.version_option(
    version=capella_ros_tools.__version__,
    prog_name="capella-ros-tools",
    message="%(prog)s %(version)s",
)
@click.argument(
    "path-to-msgs-root",
    type=click.Path(
        exists=True,
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
def msg2capella(
    path_to_msgs_root: Path,
    path_to_capella_model: str,
    layer: str,
    overlap: str,
    debug: bool,
):
    """Parse .msg files and import them to capella model."""

    converter = Msg2Capella(path_to_capella_model, layer, "keep")
    current_root = converter.serializer.data

    ros_interfaces = ParseMessagesPkg.from_pkg_folders(
        PATH.joinpath("ros_interfaces")
    )
    current_root_struct = ParseMessagesPkg(
        {}, {ROS_INTERFACES: ros_interfaces}
    )

    converter.add_objects(current_root_struct, current_root)

    converter.overlap = overlap
    current_root_struct = ParseMessagesPkg.from_pkg_folders(path_to_msgs_root)
    converter.add_objects(current_root_struct, current_root)
    converter.add_relations(current_root_struct, current_root)

    if debug:
        click.echo(converter.serializer.data)
    else:
        converter.serializer.save_changes()
