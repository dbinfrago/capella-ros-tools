# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Main entry point into rosidl2capella."""
import click

import rosidl2capella
from rosidl2capella import synchronize
from rosidl2capella.capella_wrapper import CapellaWrapper
from rosidl2capella.idl_model import IDLModel


@click.command()
@click.version_option(
    version=rosidl2capella.__version__,
    prog_name="rosidl2capella",
    message="%(prog)s %(version)s",
)
@click.argument(
    "path_to_msg_model",
    type=click.Path(
        exists=True,
        file_okay=False,
        readable=True,
        resolve_path=True,
        path_type=str,
    ),
)
@click.argument(
    "path_to_capella_model",
    type=click.Path(
        exists=True,
        file_okay=False,
        readable=True,
        resolve_path=True,
        path_type=str,
    ),
)
@click.argument(
    "layer",
    type=click.Choice(["oa", "sa", "la", "pa"], case_sensitive=False),
    required=True,
)
def main(path_to_msg_model, path_to_capella_model, layer):
    """Console script for rosidl2capella."""
    msg_model = IDLModel.from_msg_model(path_to_msg_model)
    capella_wrapper = CapellaWrapper(path_to_capella_model, layer)
    overlap = synchronize.calculate_overlap(
        msg_model, capella_wrapper.as_idlmodel
    )
    while True:
        match click.prompt(
            "There are overlaps between the models. Keep Capella Model (c), Accept IDL (i), Abort (a)?",
            type=click.Choice(["c", "i", "a"], case_sensitive=False),
        ):
            case "c":
                msg_model.delete_from_model(overlap)
                break
            case "i":
                capella_wrapper.delete_from_capella_model(overlap)
                break
            case "a":
                click.echo("Aborted!")
                return
            case _:
                continue

    capella_wrapper.create_packages(set(msg_model.packages.keys()))

    for pkg_name, package in msg_model.packages.items():
        capella_wrapper.create_classes(package.classes, pkg_name)
        capella_wrapper.create_types(package.types, pkg_name)
        capella_wrapper.create_basic_types(package.basic_types, pkg_name)

    all_classes = {}
    for pkg in msg_model.packages.values():
        all_classes |= pkg.classes

    for package_name, package in msg_model.packages.items():
        for class_name, (_, properties) in package.classes.items():
            for prop in properties:
                _, prop_type, type_pkg, _, _, _ = prop
                type_pkg = type_pkg or package_name
                if prop_type in msg_model.packages[type_pkg].classes:
                    try:
                        capella_wrapper.create_composition(
                            class_name, prop, package_name
                        )
                    except KeyError:
                        print(class_name, prop, package_name)
                else:
                    capella_wrapper.create_attribute(
                        class_name, prop, package_name
                    )

    if click.confirm(
        "Changes cannot be made undone. Do you want to continue?", abort=True
    ):
        click.echo("Changes saved to Capella Model!")
        capella_wrapper.save_changes()
    else:
        click.echo("Changes discarded!")
        return


if __name__ == "__main__":
    main()
