# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into Capella ROS Tools."""

import pathlib
import sys

import click

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
    "msg_path",
    type=click.Path(),
    required=True,
)
@click.argument(
    "capella_path",
    type=click.Path(exists=True),
    required=True,
)
@click.argument(
    "layer",
    type=click.Choice(["oa", "la", "sa", "pa"], case_sensitive=False),
    required=True,
)
@click.option(
    "--exists-action",
    "action",
    type=click.Choice(
        ["skip", "replace", "abort", "ask"], case_sensitive=False
    ),
    default="ask" if sys.stdin.isatty() else "abort",
    help="Default action when an element already exists.",
)
@click.option(
    "--no-deps",
    "no_deps",
    is_flag=True,
    help="Don’t install message dependencies.",
)
@click.option("--port", type=int, help="Open model viewer on given port.")
def import_msgs(
    msg_path: str,
    capella_path: str,
    layer: str,
    action: str,
    no_deps: bool,
    port: int,
) -> None:
    """Import ROS messages into a Capella data package.

    MSG_PATH: Path to folder with .msg files.
    CAPELLA_PATH: Path to Capella model.
    LAYER: Layer of Capella model to import elements to.
    """
    from capellambse import filehandler

    from capella_ros_tools.scripts import import_msgs as importer
    from capella_ros_tools.viewer import app

    msg_filehandler = filehandler.get_filehandler(msg_path).rootdir

    converter = importer.Importer(
        msg_filehandler, capella_path, layer, action, no_deps
    )
    converter()

    if port:
        app.start(converter.capella.model, layer)


@cli.command("export")
@click.argument("capella_path", type=click.Path(), required=True)
@click.argument(
    "layer",
    type=click.Choice(["oa", "la", "sa", "pa"], case_sensitive=False),
    required=True,
)
@click.argument(
    "msg_path", type=click.Path(path_type=pathlib.Path), required=True
)
def export_capella(
    capella_path: str,
    layer: str,
    msg_path: pathlib.Path,
):
    """Export Capella data package to ROS messages.

    CAPELLA_PATH: Path to Capella model.
    LAYER: Layer of Capella model to export elements from.
    MSG_PATH: Path to output folder for .msg files.
    """
    from capella_ros_tools.scripts import export_capella as exporter

    converter = exporter.Exporter(capella_path, layer, msg_path)
    converter()


if __name__ == "__main__":
    cli()
