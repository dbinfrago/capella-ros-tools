# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Serializer for IDL messages."""
from pathlib import Path

from capella_ros_tools.modules.messages import (
    BaseMessageDef,
    BaseMessagePkgDef,
)


class MessageDef(BaseMessageDef):
    """Message definition for a ROS message."""

    def to_msg_file(self, msg_file: Path):
        """Write message to file."""
        msg_file.write_text(self.to_msg_string())

    def to_msg_string(self) -> str:
        """Convert message to string."""
        msg_string = "\n".join(self.annotations) + "\n\n"
        for enum in self.enums:
            msg_string += (
                f"# name: {enum.name}" + "\n".join(enum.annotations) + "\n"
            )
            msg_string += (
                "\n".join(
                    [
                        f"{value.type.name} {value.name} = {value.value}"
                        + "\n".join(self.annotations)
                        for value in enum.values
                    ]
                )
                + "\n\n"
            )

        for field in self.fields:
            msg_string += (
                f"{(field.type.pkg_name + '/') if field.type.pkg_name else ''}"
            )
            msg_string += f"{field.type.name}"
            if field.type.array_size == float("inf"):
                msg_string += "[]"
            elif field.type.array_size:
                msg_string += f"[{field.type.array_size}]"
            msg_string += (
                f" {field.name}" + "\n".join(self.annotations) + "\n\n"
            )

        return msg_string


class MessagePkgDef(BaseMessagePkgDef):
    """Message package definition for ROS message package."""

    def to_msg_folder(self, msg_pkg_dir: Path):
        """Write message package to folder."""
        msg_pkg_dir.mkdir(parents=True, exist_ok=True)
        for msg in self.messages:
            msg.to_msg_file(msg_pkg_dir / f"{msg.name}.msg")
        for pkg in self.packages:
            pkg.to_msg_folder(msg_pkg_dir / pkg.name)

    def to_pkg_folder(self, pkg_dir: Path):
        """Write packages to folder."""
        pkg_dir.mkdir(parents=True, exist_ok=True)
        for pkg in self.packages:
            pkg.to_msg_folder(pkg_dir / pkg.name / "msg")
