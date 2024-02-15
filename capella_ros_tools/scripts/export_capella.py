# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Tool for exporting a Capella data package to ROS messages."""
import logging
import pathlib

from capellambse.model.crosslayer import information

from capella_ros_tools import capella, messages

logger = logging.getLogger(__name__)


class Exporter:
    """Class for exporting a Capella data package as ROS messages."""

    def __init__(
        self, capella_path: str, layer: str, output_path: pathlib.Path
    ):
        self.capella = capella.CapellaDataPackage(capella_path, layer)
        output_path.mkdir(parents=True, exist_ok=True)
        self.msg_path = output_path

    def _handle_pkg(
        self,
        current_pkg: information.DataPkg,
        current_path: pathlib.Path,
    ):
        for cls_obj in current_pkg.classes:
            cls_def = messages.MessageDef(
                cls_obj.name, [], [], cls_obj.description
            )
            for prop_obj in cls_obj.owned_properties:
                type_def = messages.TypeDef(
                    prop_obj.type.name,
                    messages.Range(
                        prop_obj.min_card.value, prop_obj.max_card.value
                    ),
                )
                prop_def = messages.FieldDef(
                    type_def, prop_obj.name, prop_obj.description
                )
                cls_def.fields.append(prop_def)
            (current_path / f"{cls_obj.name}.msg").write_text(str(cls_def))

        for enum_obj in current_pkg.enumerations:
            enum_def = messages.EnumDef(
                enum_obj.name, [], enum_obj.description
            )
            for i, lit_obj in enumerate(enum_obj.owned_literals):
                try:
                    type_name = lit_obj.value.type.name
                except AttributeError:
                    type_name = "uint8"
                try:
                    literal_value = lit_obj.value.value
                except AttributeError:
                    literal_value = i
                type_def = messages.TypeDef(
                    type_name, messages.Range("1", "1")
                )
                lit_def = messages.ConstantDef(
                    type_def,
                    lit_obj.name,
                    literal_value,
                    lit_obj.description,
                )
                enum_def.literals.append(lit_def)
            (current_path / f"{enum_obj.name}.msg").write_text(str(enum_def))

        for pkg_obj in current_pkg.packages:
            pkg_path = current_path / pkg_obj.name
            pkg_path.mkdir(parents=True, exist_ok=True)
            self._handle_pkg(pkg_obj, pkg_path)

    def __call__(self):
        """Export the Capella data package as ROS messages."""
        self._handle_pkg(self.capella.data_package, self.msg_path)
