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
        msg_string = "\n".join(self.annotations) + "\n"
        msg_string += (
            "\n".join([f"{f.type} {f.name}" for f in self.fields]) + "\n\n"
        )
        msg_string += (
            "\n\n".join([f"{e.name}\n{e.values}" for e in self.enums]) + "\n\n"
        )
        return msg_string


class MessagePkgDef(BaseMessagePkgDef):
    """Message package definition for ROS message package."""

    def to_msg_folder(self, msg_pkg_dir: Path):
        """Write message package to folder."""
        msg_pkg_dir.mkdir(parents=True, exist_ok=True)
        for msg in self.messages:
            msg.to_msg_file(msg_pkg_dir / f"{msg.name}.msg")
