# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into Capella ROS Tools."""

import io
import pathlib

import capellambse
import click
from capellambse import cli_helpers, decl

import capella_ros_tools
from capella_ros_tools import exporter, importer


@click.group()
@click.version_option(
    version=capella_ros_tools.__version__,
    prog_name="capella-ros-tools",
    message="%(prog)s %(version)s",
)
def cli():
    """Console script for Capella ROS Tools."""


@cli.command("import")
@click.option(
    "-i",
    "--input",
    type=str,
    required=True,
    help="Path to the ROS message package.",
)
@click.option(
    "-m",
    "--model",
    type=cli_helpers.ModelCLI(),
    required=True,
    help="Path to the Capella model.",
)
@click.option(
    "-l",
    "--layer",
    type=click.Choice(["oa", "la", "sa", "pa"], case_sensitive=False),
    required=True,
    help="The layer to import the messages to.",
)
@click.option(
    "--no-deps",
    "no_deps",
    is_flag=True,
    help="Don’t install message dependencies.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=pathlib.Path, dir_okay=False),
    help="Output file path for decl YAML.",
)
def import_msgs(
    input: str,
    model: capellambse.MelodyModel,
    layer: str,
    no_deps: bool,
    output: pathlib.Path,
) -> None:
    """Import ROS messages into a Capella data package."""

    root_uuid = getattr(model, layer).data_package.uuid
    types_uuid = model.sa.data_package.uuid

    yml = importer.Importer(input, no_deps).to_yaml(root_uuid, types_uuid)
    if output:
        output.write_text(yml, encoding="utf-8")
    else:
        decl.apply(model, io.StringIO(yml))
        model.save()


@cli.command("export")
@click.option(
    "-m",
    "--model",
    type=cli_helpers.ModelCLI(),
    required=True,
    help="Path to the Capella model.",
)
@click.option(
    "-l",
    "--layer",
    type=click.Choice(["oa", "la", "sa", "pa"], case_sensitive=False),
    required=True,
    help="The layer to export the model objects from.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=pathlib.Path, file_okay=False),
    default=pathlib.Path.cwd() / "data-package",
    help="Output directory for the .msg files.",
)
def export_capella(
    model: capellambse.MelodyModel,
    layer: str,
    output: pathlib.Path,
):
    """Export Capella data package to ROS messages."""
    current_pkg = getattr(model, layer).data_package
    exporter.export(current_pkg, output)


if __name__ == "__main__":
    cli()
