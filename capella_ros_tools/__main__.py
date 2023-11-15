# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into capella-ros-tools."""
import click

import capella_ros_tools
from capella_ros_tools.msg2capella import msg2capella

# from capella_ros_tools.capella2msg import capella2msg


@click.command()
@click.version_option(
    version=capella_ros_tools.__version__,
    prog_name="capella-ros-tools",
    message="%(prog)s %(version)s",
)
def main():
    """Console script for capella-ros-tools."""


if __name__ == "__main__":
    msg2capella()
    # capella2msg()
