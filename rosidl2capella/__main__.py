# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into rosidl2capella."""

import click

import rosidl2capella


@click.command()
@click.version_option(
    version=rosidl2capella.__version__,
    prog_name="rosidl2capella",
    message="%(prog)s %(version)s",
)
def main():
    """Console script for rosidl2capella."""


if __name__ == "__main__":
    main()
