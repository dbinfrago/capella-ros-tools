# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Serializer for ROS messages."""

from pathlib import Path

from . import MessageDef, MessagesPkg


class SerializeMessageDef(MessageDef):
    """Serializer for message files."""

    def to_msg_file(self, file: Path) -> None:
        """Write message definition to message file."""
        description = "# " + self.description.replace("\n", "\n# ") + "\n"
        props = "\n".join(
            f"{p.typedir+'/' if p.typedir else ''}{p.type}"
            f"{'[]' if p.min != p.max else ''} {p.name}\t"
            f"{'# ' if p.comment else ''}{p.comment}"
            for p in self.props
        )
        file.write_text(description + "\n" + props)

    def to_type_file(self, file: Path) -> None:
        """Write message definition to message file."""
        description = "# " + self.description.replace("\n", "\n# ") + "\n"
        props = "\n".join(
            f"{p.type} {file.stem + '_' + p.name}\t= {p.value}\t"
            f"{'# ' if p.comment else ''}{p.comment}"
            for p in self.props
        )
        file.write_text(description + "\n" + props)


class SerializeMessagesPkg(MessagesPkg):
    """Serializer for message packages."""

    def to_msg_folder(self, path_to_pkg_root: Path) -> None:
        """Write message package to message package."""
        path_to_pkg_root.mkdir(parents=True, exist_ok=True)
        for msg_name, msg in self.messages.items():
            msg_file = path_to_pkg_root.joinpath(msg_name + ".msg")
            if path_to_pkg_root.name == "types":
                msg.to_type_file(msg_file)
            else:
                msg.to_msg_file(msg_file)

        for pkg_name, pkg in self.packages.items():
            new_path = path_to_pkg_root.joinpath(pkg_name)
            new_path.mkdir(parents=True, exist_ok=True)
            pkg.to_msg_folder(new_path)
