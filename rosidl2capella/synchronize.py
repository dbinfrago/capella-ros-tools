# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Synchronize ROS message definitions with Capella data model."""
from rosidl2capella.capella_wrapper import CapellaWrapper
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


class MSGS2Capella:
    """Synchronize ROS message definitions with Capella data model."""

    def __init__(
        self, path_to_msg_model: str, path_to_capella_model: str, layer: str
    ) -> None:
        self.capella_wrapper = CapellaWrapper(path_to_capella_model, layer)
        self.msg_model = IDLModel.from_msg_model(path_to_msg_model)
        self.capella_model = self.capella_wrapper.as_idlmodel

    def resolve_overlap(self):
        """Resolve overlap between IDL models."""

    def sync_models(self):
        """Synchronize IDL models."""
