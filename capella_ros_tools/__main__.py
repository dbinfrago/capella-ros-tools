# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into Capella ROS Tools."""

import io
import logging
import pathlib
import uuid

import capellambse
import click
from capellambse import cli_helpers, decl

import capella_ros_tools
from capella_ros_tools import exporter, importer, logger


@click.group()
@click.version_option(
    version=capella_ros_tools.__version__,
    prog_name="capella-ros-tools",
    message="%(prog)s %(version)s",
)
def cli() -> None:
    """Console script for Capella ROS Tools."""

    logging.basicConfig(level=logging.INFO)


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
    help="The layer to import the messages to.",
)
@click.option(
    "-r",
    "--root",
    type=click.UUID,
    help="The UUID of the root package to import the messages to.",
)
@click.option(
    "-t",
    "--types",
    type=click.UUID,
    help="The UUID of the types package to import the created data types to.",
)
@click.option(
    "--no-deps",
    "no_deps",
    is_flag=True,
    help="Don't install message dependencies.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=pathlib.Path, dir_okay=False),
    help="Produce a declarative YAML instead of modifying the source model.",
)
@click.option(
    "--license-header",
    type=click.Path(path_type=pathlib.Path, dir_okay=False),
    help="Ignore the license header from the given file when importing msgs.",
)
@click.option(
    "--description-regex",
    type=str,
    help="Regular expression to extract description from the file .",
)
@click.option(
    "--dependency-json",
    type=click.Path(path_type=pathlib.Path, dir_okay=False),
    help="A path to a JSON containing dependencies which should be imported.",
)
def import_msgs(
    *,
    input: str,
    model: capellambse.MelodyModel,
    layer: str,
    root: uuid.UUID,
    types: uuid.UUID,
    no_deps: bool,
    output: pathlib.Path,
    license_header: pathlib.Path | None,
    description_regex: str | None,
    dependency_json: pathlib.Path | None,
) -> None:
    """Import ROS messages into a Capella data package."""
    if root:
        root_uuid = str(root)
    elif layer:
        root_uuid = getattr(model, layer).data_package.uuid
    else:
        raise click.UsageError("Either --root or --layer must be provided")

    if types:
        params = {"types_uuid": str(types)}
    else:
        params = {"types_parent_uuid": model.sa.data_package.uuid}

    parsed = importer.Importer(
        input, no_deps, license_header, description_regex, dependency_json
    )
    logger.info("Loaded %d packages", len(parsed.messages.packages))

    yml = parsed.to_yaml(root_uuid, **params)
    if output:
        logger.info("Writing declarative YAML to file %s", output)
        output.write_text(yml, encoding="utf-8")
    else:
        logger.info("Writing to model %s", model.name)
        decl.apply(model, io.StringIO(yml))
        model.save()


@cli.command("export")
@click.option(
    "-m",
    "--model",
    type=cli_helpers.ModelCLI(),
    required=True,
    help="Path to the Capella model.",
    envvar="CAPELLA_ROS_TOOLS_MODEL",
)
@click.option(
    "-l",
    "--layer",
    type=click.Choice(["oa", "la", "sa", "pa"], case_sensitive=False),
    help="The layer to export the model objects from.",
    envvar="CAPELLA_ROS_TOOLS_LAYER",
)
@click.option(
    "-r",
    "--root",
    type=click.UUID,
    help="The UUID of the root package to import the messages from.",
    envvar="CAPELLA_ROS_TOOLS_ROOT_PACKAGE",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(
        path_type=pathlib.Path, file_okay=True, dir_okay=False, readable=True
    ),
    help="Path to the configuration file.",
    envvar="CAPELLA_ROS_TOOLS_EXPORT_CONFIG",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=pathlib.Path, file_okay=False),
    default=pathlib.Path.cwd() / "data-package",
    help="Output directory for the .msg files.",
)
@click.option(
    "--contact-email",
    type=str,
    default="dummy@dummy",
    help="E-Mail address to be placed in the package.xml files.",
    envvar="CAPELLA_ROS_TOOLS_CONTACT_EMAIL",
)
@click.option(
    "--maintainer",
    type=str,
    default="Dummy Company",
    help="Name of the maintainer used in the package.xml files.",
    envvar="CAPELLA_ROS_TOOLS_MAINTAINER",
)
@click.option(
    "-p",
    "--project-name",
    type=str,
    default="custom_ros_msgs",
    help="Project name being used in CMake and package.xml files.",
    envvar="CAPELLA_ROS_TOOLS_PROJECT_NAME",
)
@click.option(
    "--generate-cmake",
    type=bool,
    default=False,
    is_flag=True,
    help="Decide whether experimental cmake files should be generated.",
    envvar="CAPELLA_ROS_TOOLS_GENERATE_CMAKE",
)
def configured_export(
    model: capellambse.MelodyModel,
    config: pathlib.Path | None,
    layer: str | None,
    root: str | None,
    output: pathlib.Path,
    contact_email: str,
    maintainer: str,
    project_name: str,
    generate_cmake: bool,
) -> None:
    """Export Capella data package to ROS messages."""
    if config:
        conf = exporter.load_config(config, model)
    else:
        if root:
            root_package = model.search("DataPkg").by_uuid(str(root))
        elif layer:
            root_package = getattr(model, layer).data_package
        else:
            logger.error(
                "Neither config nor root package nor layer specified."
            )
            return -1
        if not isinstance(root_package, capellambse.model.ModelElement):
            logger.error("Failed to find root package.")
            return -1
        conf = exporter.ExporterConfig(
            packages={
                exporter.Exporter.make_snake_case(
                    root_package.name
                ): root_package.uuid
            },
            build_ins={},
            custom_packages={},
            custom_types={},
        )
    if conf.packages and (root or layer):
        logger.warning(
            "Your config has packages defined, will ignore root/layer for that reason."
        )

    _exporter = exporter.Exporter(
        conf.packages,
        conf.build_ins,
        conf.custom_packages,
        conf.custom_types,
        model,
        generate_cmake,
    )
    export_data, dependency_map = _exporter.prepare_export_data()
    _exporter.export_ros_pkgs(
        output,
        project_name,
        export_data,
        dependency_map,
        contact_email,
        maintainer,
    )


if __name__ == "__main__":
    cli()
