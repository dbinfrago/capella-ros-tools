# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into capella_ros_tools."""

import sys
import typing as t
from pathlib import Path

import capellambse
import click

import capella_ros_tools
from capella_ros_tools.scripts import capella2msg, msg2capella
from capella_ros_tools.snapshot import app


@click.group(context_settings={"default_map": {}})
@click.version_option(
    version=capella_ros_tools.__version__,
    prog_name="capella-ros-tools",
    message="%(prog)s %(version)s",
)
def cli():
    """CLI for capella-ros-tools."""


@cli.command("import")
@click.argument(
    "msg_path", type=str, required=True, help="Path to ROS messages."
)
@click.argument(
    "capella_path",
    type=click.Path(path_type=Path),
    required=True,
    help="Path to Capella model.",
)
@click.argument(
    "layer",
    type=click.Choice(["oa", "la", "sa", "pa"], case_sensitive=False),
    required=True,
    help="Layer of Capella data package.",
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
@click.option("--port", type=int, help="Port for HTML display.")
def import_msg(
    msg_path: t.Any,
    capella_path: Path,
    layer: str,
    action: str,
    no_deps: bool,
    port: int,
):
    """Import ROS messages into Capella data package."""

    if not Path(msg_path).exists():
        msg_path = capellambse.filehandler.get_filehandler(msg_path).rootdir

    converter: t.Any = msg2capella.Converter(
        msg_path, capella_path, layer, action, no_deps
    )
    converter.convert()

    if port:
        app.start(converter.model.model, layer, port)


@cli.command("export")
@click.argument("capella_path", type=str, required=True)
@click.argument(
    "layer",
    type=click.Choice(["oa", "la", "sa", "pa"], case_sensitive=False),
    required=True,
)
@click.argument("msg_path", type=click.Path(path_type=Path), required=True)
@click.option(
    "--exists-action",
    "action",
    type=click.Choice(
        ["keep", "overwrite", "abort", "ask"], case_sensitive=False
    ),
    default="ask" if sys.stdin.isatty() else "abort",
    help="Default action when an element already exists.",
)
def export_capella(
    capella_path: t.Any,
    msg_path: Path,
    layer: str,
):
    """Export Capella data package to ROS messages."""
    if not Path(capella_path).exists():
        capella_path = capellambse.filehandler.get_filehandler(capella_path)

    converter: t.Any = capella2msg.Converter(capella_path, msg_path, layer)
    converter.convert()


if __name__ == "__main__":
    cli()
