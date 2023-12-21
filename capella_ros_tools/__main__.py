# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into capella_ros_tools."""

import sys
import typing as t
from pathlib import Path

import capellambse
import click

import capella_ros_tools
from capella_ros_tools.display import app
from capella_ros_tools.scripts import capella2msg, msg2capella


@click.command()
@click.version_option(
    version=capella_ros_tools.__version__,
    prog_name="capella-ros-tools",
    message="%(prog)s %(version)s",
)
@click.option(
    "--exists-action",
    "action",
    type=click.Choice(["k", "o", "a", "c"], case_sensitive=False),
    default="c" if sys.stdin.isatty() else "a",
    help="Default action when an element already exists: (c)heck, (k)eep, (o)verwrite, (a)bort.",
)
@click.option("--port", "-p", type=int, help="Port for HTML display.")
@click.option(
    "--in",
    "-i",
    "in_",
    nargs=2,
    type=(click.Choice(["capella", "messages"]), str),
    required=True,
    help="Input file type and path.",
)
@click.option(
    "--out",
    "-o",
    nargs=2,
    type=(
        click.Choice(["capella", "messages"]),
        click.Path(path_type=Path),
    ),
    required=True,
    help="Output file type and path.",
)
@click.option(
    "--layer",
    "-l",
    type=click.Choice(["oa", "sa", "la", "pa"], case_sensitive=True),
    required=True,
    help="Layer to use.",
)
@click.option(
    "--no-deps",
    "no_deps",
    is_flag=True,
    help="Don’t install message dependencies.",
)
def cli(
    in_: tuple[str, str],
    out: tuple[str, str],
    layer: str,
    action: str,
    port: int,
    no_deps: bool,
):
    """Convert between Capella and ROS message definitions."""
    input_type, input_path = in_
    output_type, output = out

    if input_type == output_type:
        raise click.UsageError(
            "Input and output must be different file types."
        )
    if "capella" not in (input_type, output_type):
        raise click.UsageError(
            "Either input or output must be a capella file."
        )
    if "messages" not in (input_type, output_type):
        raise click.UsageError(
            "Either input or output must be a messages file."
        )

    input: t.Any = Path(input_path)

    input = (
        input
        if input.exists()
        else capellambse.filehandler.get_filehandler(input_path).rootdir
    )

    msg_path, capella_path, convert_class = (
        (input, output, msg2capella.Converter)
        if input_type == "messages"
        else (output, input, capella2msg.Converter)
    )

    converter = convert_class(msg_path, capella_path, layer, action, no_deps)
    converter.convert()

    if port:
        app.start(converter.model.model, layer, port)


if __name__ == "__main__":
    cli()
