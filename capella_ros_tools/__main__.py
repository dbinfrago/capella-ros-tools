# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into Capella ROS Tools."""

import io
import pathlib

import capellambse
import click
from capellambse import cli_helpers, decl

import capella_ros_tools


@click.group()
@click.version_option(
    version=capella_ros_tools.__version__,
    prog_name="capella-ros-tools",
    message="%(prog)s %(version)s",
)
def cli():
    """Console script for Capella ROS Tools."""


@cli.command("import")
@click.argument(
    "messages",
    type=str,
    required=True,
)
@click.argument(
    "model",
    type=cli_helpers.ModelCLI(),
    required=True,
)
@click.argument(
    "layer",
    type=click.Choice(["oa", "la", "sa", "pa"], case_sensitive=False),
    required=True,
)
@click.option(
    "--no-deps",
    "no_deps",
    is_flag=True,
    help="Don’t install message dependencies.",
)
@click.option("--port", type=int, help="Open model viewer on given port.")
def import_msgs(
    messages: str,
    model: capellambse.MelodyModel,
    layer: str,
    no_deps: bool,
    port: int,
) -> None:
    """Import ROS messages into a Capella data package.

    MESSAGES: File path or git URL to ROS messages.
    MODEL: Path to Capella model.
    LAYER: Layer of Capella model to import elements to.
    """

    from capella_ros_tools.scripts import import_msgs as importer

    root_uuid = getattr(model, layer).uuid
    types_uuid = model.sa.data_package.uuid

    yml = importer.Importer(messages, no_deps)(root_uuid, types_uuid)
    decl.apply(model, io.StringIO(yml))

    if port:
        raise NotImplementedError("Open model with model explorer.")


@cli.command("export")
@click.argument("model", type=cli_helpers.ModelCLI, required=True)
@click.argument(
    "layer",
    type=click.Choice(["oa", "la", "sa", "pa"], case_sensitive=False),
    required=True,
)
@click.argument(
    "messages", type=click.Path(path_type=pathlib.Path), required=True
)
def export_capella(
    model: capellambse.MelodyModel,
    layer: str,
    msg_path: pathlib.Path,
):
    """Export Capella data package to ROS messages.

    CAPELLA_PATH: Path to Capella model.
    LAYER: Layer of Capella model to export elements from.
    MESSAGES: Path to output folder for .msg files.
    """
    from capella_ros_tools.scripts import export_capella as exporter

    exporter.Exporter(model, layer, msg_path)()


if __name__ == "__main__":
    cli()
