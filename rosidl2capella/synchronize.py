# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Synchronize ROS message definitions with Capella data model."""
from rosidl2capella.idl_model import IDLModel, IDLPackage


def calculate_overlap(
    left: IDLModel, right: IDLModel
) -> dict[str, IDLPackage]:
    """Calculate overlap between two IDL models."""
    overlap = {}
    for pkg_name, left_package in left.packages.items():
        right_package = right.packages.get(pkg_name)
        if right_package:
            overlap[pkg_name] = IDLPackage(
                left_package.classes.keys() & right_package.classes.keys(),
                left_package.types.keys() & right_package.types.keys(),
                left_package.basic_types & right_package.basic_types,
            )
    return overlap
