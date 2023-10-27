# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Parser for ROS message files."""
import os
import re
from pathlib import Path

RE_TNC = re.compile(
    r"^([A-Za-z0-9\[\]\/_]+).*?([A-Za-z0-9_]+)(?:.*?# ([^\n]+))?"
)
RE_NAME = re.compile(r"([a-zA-Z0-9]+)[.]msg")
RE_ENUM = re.compile(
    r"^([A-Za-z0-9]+).*?([A-Za-z0-9_]+).*?= ([0-9]+)(?:.*?# ([^\n]+))?"
)
RE_COMMENT = re.compile(r"cf. ([a-zA-Z0-9_]+)(?:, ([a-zA-Z0-9_]+))?")


class MessageDef:
    """Message definition."""

    def __init__(self, name, description, props, is_type):
        self.name = name
        self.description = description
        self.props = props
        self.is_type = is_type

    @property
    def as_struct(self):
        """Return message definition as struct."""
        if self.is_type:
            return (self.description, self.props)
        out = []
        for prop, prop_type_raw, comment in self.props:
            p = prop_type_raw.split("[", 1)
            min_card = "0" if len(p) > 1 else "1"
            max_card = p[1].replace("]", "") if len(p) > 1 else "1"
            match = RE_COMMENT.search(comment)
            enum, subenum = match.groups() if match else (None, None)
            type_path = list(p[0].split("/", 1))
            prop_type = (
                re.sub("_XXX$", "", subenum)
                if subenum
                else enum
                if enum
                else type_path[-1]
            )
            type_pkg = type_path[0] if len(type_path) > 1 else ""
            out.append(
                (prop, prop_type, type_pkg, min_card, max_card, comment)
            )
        return (self.description, out)

    @classmethod
    def from_msg_file(cls, filename, is_type):
        """Create message definition from message file."""
        with open(filename) as fh:
            raw_msg = fh.read()

        lines = raw_msg.split("\n")
        msg = []
        comment = []
        for line in lines:
            if line.startswith("#"):
                comment.append(line)
            else:
                msg.extend(lines[lines.index(line) :])
                break
        description = "\n".join(comment).replace("#", "").strip()
        name = RE_NAME.findall(str(filename))[0]
        if is_type:
            blocks = "\n".join(msg).split("\n\n")
            out = []
            for block in blocks:
                lines = block.split("\n")
                pairs = [
                    tnvc for line in lines for tnvc in RE_ENUM.findall(line)
                ]
                props = [(n, t, v, c) for t, n, v, c in pairs]
                commonprefix = os.path.commonprefix(
                    [prop[0] for prop in props]
                )
                name = (
                    commonprefix.rpartition("_")[0]
                    if len(blocks) > 1
                    else name
                )
                props = [
                    (prop[0].replace(commonprefix, ""), *prop[1:])
                    for prop in props
                ]
                out.append(cls(name, description, props, is_type))
            return out
        pairs = [tnc for line in msg for tnc in RE_TNC.findall(line)]
        props = [(n, t, c) for t, n, c in pairs]
        return cls(name, description, props, is_type)


class MessagesPkg:
    """Messages package."""

    def __init__(self, messages):
        self.messages = messages

    def __getitem__(self, key):
        """Get message by key."""
        return self.messages[key]

    def __contains__(self, key):
        """Check if message is in package."""
        return key in self.messages

    @property
    def as_structs(self):
        """Return messages as structs."""
        return {k: v.as_struct for k, v in self.messages.items()}

    @classmethod
    def from_msg_folder(cls, path_to_pkg_root, get_types=False):
        """Create messages package from message folder."""
        if get_types:
            msg_files = list(Path(path_to_pkg_root).rglob("types/*.msg"))
        else:
            msg_files = [
                f
                for f in Path(path_to_pkg_root).rglob("**/*.msg")
                if "types" not in f.parts
            ]
        out = cls({})
        for msg in map(
            lambda x: MessageDef.from_msg_file(x, get_types), msg_files
        ):
            if isinstance(msg, list):
                for m in msg:
                    out.messages[m.name] = m
            else:
                out.messages[msg.name] = msg
        return out
