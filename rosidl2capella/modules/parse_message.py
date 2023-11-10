# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Parser for ROS messages."""
import os
import re
from pathlib import Path

from . import EnumValue, MessageDef, MessagesPkg, MsgProp

RE_TNC = re.compile(
    r"^([A-Za-z0-9\[\]\/_]+).*?([A-Za-z0-9_]+)(?:.*?# ([^\n]+))?"
)
RE_ENUM = re.compile(
    r"^([A-Za-z0-9]+).*?([A-Za-z0-9_]+).*?= ([0-9]+)(?:.*?# ([^\n]+))?"
)
RE_COMMENT = re.compile(r"cf. ([a-zA-Z0-9_]+)(?:, ([a-zA-Z0-9_]+))?")


class ParseMessageDef(MessageDef):
    """Parser for message files."""

    @property
    def as_struct(self) -> tuple:
        """Return message definition as struct."""
        return (self.description, self.props)

    @classmethod
    def from_msg_file(cls, file: Path) -> list:
        """Create message definition from message file."""
        raw_msg = file.read_text()
        lines = raw_msg.split("\n")
        for i, line in enumerate(lines):
            if not line.startswith("#"):
                break
        else:
            i = 0
        description = "\n".join(l.lstrip("#").strip() for l in lines[:i])
        props = []
        for line in lines[i:]:
            for prop_type_raw, prop_name, comment in RE_TNC.findall(line):
                p = prop_type_raw.split("[", 1)
                min_card = "0" if len(p) > 1 else "1"
                max_card = p[1].replace("]", "") if len(p) > 1 else "1"
                match = RE_COMMENT.search(comment)
                filename, commonprefix = (
                    match.groups() if match else (None, None)
                )
                type_path = list(p[0].split("/", 1))
                if commonprefix:
                    prop_type = re.sub("_XXX$", "", commonprefix)
                else:
                    prop_type = filename if filename else type_path[-1]
                type_pkg = type_path[0] if len(type_path) > 1 else ""
                props.append(
                    MsgProp(
                        prop_name,
                        prop_type,
                        type_pkg,
                        min_card,
                        max_card,
                        comment,
                    )
                )

        return [cls(file.stem, description, props)]

    @classmethod
    def from_type_file(cls, file: Path) -> list:
        """Create message definition from type file."""
        raw_msg = file.read_text()
        lines = raw_msg.split("\n")
        for i, line in enumerate(lines):
            if not line.startswith("#"):
                break
        else:
            i = 0
        description = "\n".join(l.lstrip("#").strip() for l in lines[:i])
        blocks = "\n".join(lines[i:]).split("\n\n")
        out = []
        for block in blocks:
            lines = block.split("\n")
            props = [
                (n, t, v, c)
                for line in lines
                for (t, n, v, c) in RE_ENUM.findall(line)
            ]
            commonprefix = os.path.commonprefix([prop[0] for prop in props])
            name = (
                commonprefix.rpartition("_")[0]
                if len(blocks) > 1
                else file.stem
            )
            props = [
                EnumValue(prop[0].replace(commonprefix, ""), *prop[1:])
                for prop in props
            ]
            out.append(cls(name, description, props))
        return out


class ParseMessagesPkg(MessagesPkg):
    """Parse messages package."""

    @property
    def as_structs(self) -> tuple:
        """Return package as structs."""
        messages = {k: v.as_struct for k, v in self.messages.items()}
        packages = {k: v.as_structs for k, v in self.packages.items()}
        return (messages, packages)

    @classmethod
    def from_msg_folder(cls, path_to_pkg_root: Path):
        """Create package package from message folder."""
        out = cls({}, {})
        func = (
            ParseMessageDef.from_type_file
            if "types" in path_to_pkg_root.parts
            else ParseMessageDef.from_msg_file
        )
        for f in path_to_pkg_root.iterdir():
            if f.name.endswith(".msg"):
                msg = func(f)
                for m in msg:
                    out.messages[m.name] = m
            elif f.is_dir():
                out.packages[f.name] = cls.from_msg_folder(f)

        return out

    @classmethod
    def from_pkg_folders(cls, path_to_root: Path):
        """Create package from package folder."""
        out = cls({}, {})
        for dir in path_to_root.rglob("**/msg/"):
            out.packages[dir.parent.name] = ParseMessagesPkg.from_msg_folder(
                dir
            )
        return out
