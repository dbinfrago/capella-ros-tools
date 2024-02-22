# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Tool for parsing ROS messages."""

from __future__ import annotations

import os
import pathlib
import re
import typing as t

from capellambse.filehandler import abc

PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR = "/"
COMMENT_DELIMITER = "#"
CONSTANT_SEPARATOR = "="
UPPER_BOUND_TOKEN = "<="

VALID_MESSAGE_NAME_PATTERN = "[A-Z][A-Za-z0-9]*"
VALID_CONSTANT_NAME_PATTERN = "[A-Z](?:[A-Z0-9_]*[A-Z0-9])?"
VALID_REF_COMMENT_PATTERN = re.compile(
    r"cf\.\s*"
    rf"({VALID_MESSAGE_NAME_PATTERN})"
    r"(?:,\s*"
    rf"({VALID_CONSTANT_NAME_PATTERN}))?"
)

HTML_TAG_PATTERN = re.compile("<.*?>")


def _cleanhtml(raw_html: str):
    return re.sub(HTML_TAG_PATTERN, "", raw_html)


class Range(t.NamedTuple):
    """Define range of values."""

    min: str
    max: str


class TypeDef:
    """Type definition."""

    def __init__(
        self,
        name: str,
        card: Range,
        range: Range | None = None,
        package: str | None = None,
    ) -> None:
        self.name = name
        self.card = card
        self.range = range
        self.package = package

    def __str__(self) -> str:
        """Return string representation of the type."""
        out = self.name
        if self.range:
            out += f"[{UPPER_BOUND_TOKEN}{self.range.max}]"
        elif self.card.min != self.card.max:
            out += f"[{self.card.max if self.card.max != '*' else ''}]"
        if self.package:
            out = f"{self.package}{PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR}{out}"
        return out

    @classmethod
    def from_string(cls, type_str: str) -> TypeDef:
        """Create a type definition from a string."""
        if type_str.endswith("]"):
            name, max_card = type_str.split("[")
            max_card = max_card.rstrip("]")
            if max_card.startswith(UPPER_BOUND_TOKEN):
                range = Range("0", max_card[len(UPPER_BOUND_TOKEN) :])
                card = Range("1", "1")
            else:
                range = None
                max_card = max_card if max_card else "*"
                card = Range("0", max_card)
        else:
            name = type_str
            card = Range("1", "1")
            range = None

        if (
            len(name_split := name.split(PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR))
            > 1
        ):
            package, name = name_split
        else:
            package = None

        return cls(name, card, range, package)


class FieldDef:
    """Definition of a field in a ROS message."""

    def __init__(self, type: TypeDef, name: str, description: str) -> None:
        self.type = type
        self.name = name
        self.description = description

    def __str__(self) -> str:
        """Return string representation of the field."""
        out = f"{self.type} {self.name}"
        if self.description:
            out += f"    # {_cleanhtml(self.description)}"
        return out


class ConstantDef:
    """Definition of a constant in a ROS message."""

    def __init__(
        self,
        type: TypeDef,
        name: str,
        value: str,
        description: str,
    ) -> None:
        self.type = type
        self.name = name
        self.value = value
        self.description = description

    def __str__(self) -> str:
        """Return string representation of the constant."""
        out = f"{self.type} {self.name} = {self.value}"
        if self.description:
            out += f"    # {_cleanhtml(self.description)}"
        return out


class EnumDef:
    """Definition of an enum in a ROS message."""

    def __init__(
        self, name: str, literals: list[ConstantDef], description: str
    ) -> None:
        self.name = name
        self.literals = literals
        self.description = description

    def __str__(self) -> str:
        """Return string representation of the enum."""
        out = f"\n# name: {self.name}"
        if self.description:
            out += f"\n# info: {_cleanhtml(self.description)}"
        for literal in self.literals:
            out += f"\n{literal}"
        out += "\n"
        return out


def _extract_file_level_comments(
    message_string: str,
) -> t.Tuple[str, list[str]]:
    """Extract comments at the beginning of the message."""
    message_string = message_string.lstrip("\n")
    lines = message_string.splitlines()
    file_level_comments = ""

    index = 0
    for index, line in enumerate(lines):
        if not line.startswith(COMMENT_DELIMITER):
            break
        if line:
            file_level_comments += (
                f"{'<p>'+line.rstrip(COMMENT_DELIMITER).strip()+'</p>'}"
            )

    file_content = lines[index:] + [""]
    return file_level_comments, file_content


class MessageDef:
    """Definition of a ROS message."""

    def __init__(
        self,
        name: str,
        fields: list[FieldDef],
        enums: list[EnumDef],
        description: str,
    ) -> None:
        self.name = name
        self.fields = fields
        self.enums = enums
        self.description = description

    def __str__(self) -> str:
        """Return string representation of the message."""
        out = f"\n# name: {self.name}"
        if self.description:
            out += f"\n# info: {_cleanhtml(self.description)}"
        out += "\n"
        for enum in self.enums:
            out += f"{enum}"
        for field in self.fields:
            out += f"\n{field}"
        return out

    @classmethod
    def from_file(
        cls, file: pathlib.Path | abc.AbstractFilePath
    ) -> MessageDef:
        """Create message definition from a .msg file."""
        msg_name = file.stem
        msg_string = file.read_text()
        return cls.from_string(msg_name, msg_string)

    @classmethod
    def from_string(cls, msg_name: str, msg_string: str) -> MessageDef:
        """Create message definition from a string."""
        msg_comments, lines = _extract_file_level_comments(msg_string)
        msg = cls(msg_name, [], [], msg_comments)
        last_element: t.Any = msg
        block_comments = ""
        index = 0

        for line in lines:
            line = line.rstrip()
            if not line:
                # new block
                if index == 0:
                    continue
                if isinstance(last_element, ConstantDef):
                    last_element = msg.enums[-1]
                block_comments = ""
                continue

            last_index = index
            index = line.find(COMMENT_DELIMITER)
            if index == -1:
                # no comment
                comment = block_comments
            elif index == 0:
                # block comment
                if last_index != 0:
                    # new block comment
                    block_comments = ""
                block_comments += (
                    f"<p>{line[index:].rstrip(COMMENT_DELIMITER).strip()}</p>"
                )
                continue
            else:
                comment = (
                    f"<p>{line[index:].rstrip(COMMENT_DELIMITER).strip()}</p>"
                )
                line = line[:index].rstrip()
                if not line:
                    # indented comment
                    last_element.description += comment
                    continue
                comment = block_comments + comment

            type_string, _, rest = line.partition(" ")
            name, _, value = rest.partition(CONSTANT_SEPARATOR)
            name = name.rstrip()
            if value:
                # constant
                value = value.lstrip()
                if not isinstance(last_element, ConstantDef):
                    enum_def = EnumDef("", [], "")
                    msg.enums.append(enum_def)
                constant_def = ConstantDef(
                    TypeDef.from_string(type_string),
                    name,
                    value,
                    comment,
                )
                msg.enums[-1].literals.append(constant_def)
                last_element = constant_def
            else:
                # field
                field_def = FieldDef(
                    TypeDef.from_string(type_string),
                    name,
                    comment,
                )
                msg.fields.append(field_def)
                last_element = field_def

        for field in msg.fields:
            if match := VALID_REF_COMMENT_PATTERN.match(field.description):
                ref_msg_name, ref_const_name = match.groups()
                if ref_const_name:
                    field.type.name = _get_enum_identifier(
                        ref_const_name.rstrip("_XXX")
                    )
                else:
                    field.type.name = ref_msg_name

        for i, enum in enumerate(msg.enums):
            next_enum = msg.enums[i + 1] if i < len(msg.enums) - 1 else None
            enum_value_type = enum.literals[0].type.name
            if (
                next_enum
                and next_enum.literals[0].type.name == enum_value_type
                and (len(enum.literals) == 1 or len(next_enum.literals) == 1)
            ):
                enum.literals.extend(next_enum.literals)
                del next_enum

            common_prefix = os.path.commonprefix(
                [literal.name for literal in enum.literals]
            )
            if common_prefix:
                enum.name = _get_enum_identifier(common_prefix)
                for literal in enum.literals:
                    literal.name = literal.name.removeprefix(common_prefix)
            else:
                enum.name = msg_name if not msg.fields else msg_name + "Type"

            name_matched = False
            for field in msg.fields:
                if field.name.lower() == enum.name.lower():
                    field.type.name = enum.name
                    name_matched = True
                    break

            if not name_matched:
                for field in msg.fields:
                    if field.type.name == enum_value_type:
                        field.type.name = enum.name
                        break

        return msg


def _get_enum_identifier(common_prefix: str) -> str:
    """Get the identifier of an enum."""
    return "".join([x.capitalize() for x in common_prefix.split("_")])


class MessagePkgDef:
    """Definition of a ROS message package."""

    def __init__(
        self,
        name: str,
        messages: list[MessageDef],
        packages: list[MessagePkgDef],
    ) -> None:
        self.name = name
        self.messages = messages
        self.packages = packages

    @classmethod
    def from_msg_folder(
        cls, pkg_name: str, msg_path: pathlib.Path | abc.AbstractFilePath
    ) -> MessagePkgDef:
        """Create a message package definition from a folder."""
        out = cls(pkg_name, [], [])
        for msg_file in msg_path.rglob("*.msg"):
            msg_def = MessageDef.from_file(msg_file)
            out.messages.append(msg_def)
        return out
