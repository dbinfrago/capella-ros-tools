# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Parser for IDL messages."""
import os
import re
import typing as t

from . import (
    BaseMessageDef,
    BaseMessagePkgDef,
    BaseTypeDef,
    ConstantDef,
    EnumDef,
    FieldDef,
)

PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR = "/"
COMMENT_DELIMITER = "#"
CONSTANT_SEPARATOR = "="
ARRAY_UPPER_BOUND_TOKEN = "<="
STRING_UPPER_BOUND_TOKEN = "<="


PRIMITIVE_TYPES = [
    "bool",
    "byte",
    "char",
    "float32",
    "float64",
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
    "string",
    "wstring",
]


VALID_MESSAGE_NAME_PATTERN = "[A-Z][A-Za-z0-9]*"
VALID_CONSTANT_NAME_PATTERN = "[A-Z](?:[A-Z0-9_]*[A-Z0-9])?"
VALID_REF_COMMENT_PATTERN = re.compile(
    r"cf\.\s*"
    rf"({VALID_MESSAGE_NAME_PATTERN})"
    r"(?:,\s*"
    rf"({VALID_CONSTANT_NAME_PATTERN}))?"
)


class TypeDef(BaseTypeDef):
    """Type definition for a field or constant in a parsed message."""

    def __init__(self, type_string: str) -> None:
        super().__init__(type_string)

        if type_string[-1] == "]":
            # is array
            index = type_string.rindex("[")
            array_size_string = type_string[index + 1 : -1]
            if array_size_string:
                self.array_size = array_size_string.lstrip(
                    ARRAY_UPPER_BOUND_TOKEN
                )
            else:
                # dynamic array
                self.array_size = "*"

            type_string = type_string[:index]

        type_string = type_string.split(STRING_UPPER_BOUND_TOKEN, 1)[0]
        if type_string not in PRIMITIVE_TYPES:
            parts = type_string.split(PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR, 1)
            if len(parts) == 2:
                # type string contains the package name
                self.pkg_name = parts[0]
                type_string = parts[1]

        self.name = type_string


def _extract_file_level_comments(message_string: str):
    """Extract comments at the beginning of the message."""
    lines = message_string.splitlines()
    if lines and not lines[0].strip():
        lines = lines[1:]

    for index, line in enumerate(lines):
        if not line.startswith(COMMENT_DELIMITER):
            break
    else:
        index = 0

    file_content = lines[index:] + [""]
    file_level_comments = lines[:index]
    return file_level_comments, file_content


class MessageDef(BaseMessageDef):
    """Definition of a message for parsed messages."""

    @classmethod
    def from_msg_file(cls, msg_file: t.Any):
        """Create message definition from a .msg file."""
        msg_name = msg_file.stem
        message_string = msg_file.read_text()
        return cls.from_msg_string(msg_name, message_string)

    @classmethod
    def from_msg_string(cls, msg_name: str, message_string: str):
        """Create message definition from a message string."""
        message_comments, lines = _extract_file_level_comments(message_string)
        msg = cls(msg_name, [], [], message_comments)
        last_element: t.Any = msg
        current_comments: list = []
        last_index = index = -1

        for line in lines:
            line = line.rstrip()

            if not line:
                # new block
                if last_index == index == 0:
                    # comments were not used
                    msg.annotations += current_comments
                current_comments = []
                if isinstance(last_element, ConstantDef):
                    last_element = msg.enums[-1]
                continue

            last_index = index
            index = line.find(COMMENT_DELIMITER)

            if index != -1:
                # line has a comment
                comment = line[index:]
                line = line[:index]
                line_stripped = line.strip()
                if line and not line_stripped:
                    # indented comment line
                    # append to previous field/constant if available or ignore
                    last_element.annotations.append(comment)
                    continue
                line = line_stripped
                if not line:
                    # block comment
                    if last_index != index:
                        # first line of block comment
                        current_comments = []
                    # save "unused" comments for next block
                    current_comments.append(comment)
                    continue
            else:
                comment = ""

            type_string, _, rest = line.partition(" ")
            rest = rest.lstrip()
            name, _, value = rest.partition(CONSTANT_SEPARATOR)
            name = name.rstrip()
            if value:
                # line contains a constant
                value = value.lstrip()
                if not isinstance(last_element, ConstantDef):
                    msg.enums.append(EnumDef("", [], current_comments))
                msg.enums[-1].values.append(
                    ConstantDef(TypeDef(type_string), name, value, [comment])
                )
                last_element = msg.enums[-1].values[-1]
            else:
                # line contains a field
                msg.fields.append(
                    FieldDef(
                        TypeDef(type_string),
                        name,
                        current_comments + [comment],
                    )
                )
                last_element = msg.fields[-1]

        # condense and rename enums
        _process_enums(msg)

        # condense comment lines, extract special annotations
        _process_comments(msg)
        for field in msg.fields:
            _process_comments(field)
        for enum in msg.enums:
            _process_comments(enum)
            for constant in enum.values:
                _process_comments(constant)
        return msg


def _get_enum_identifier(common_prefix: str) -> str:
    return "".join([x.capitalize() for x in common_prefix.split("_")])


def _rename_enum(enum: EnumDef):
    common_prefix = os.path.commonprefix([v.name for v in enum.values])
    for v in enum.values:
        v.name = v.name.removeprefix(common_prefix)

    enum.name = _get_enum_identifier(common_prefix)


def _process_enums(msg):
    """Condense enums and rename them if necessary."""
    if len(msg.enums) == 0:
        return

    for enum in msg.enums:
        _rename_enum(enum)

    to_delete = []
    for i, enum in enumerate(msg.enums):
        # combine enums with the same name or have just 1 value
        if enum in to_delete:
            continue

        try:
            if len(enum.values) == 1:
                msg.enums[i + 1].values = enum.values + msg.enums[i + 1].values
                to_delete.append(enum)
                continue
        except IndexError:
            pass

        indeces = [
            i
            for i, other_enum in enumerate(msg.enums)
            if other_enum.name is enum.name and other_enum is not enum
        ]
        for i in indeces:
            to_delete.append(msg.enums[i])
            for value in msg.enums[i].values:
                enum.values.append(
                    ConstantDef(
                        TypeDef(value.type.name),
                        value.name,
                        value.value,
                        value.annotations.copy(),
                    )
                )

    for enum in to_delete:
        msg.enums.remove(enum)

    for enum in msg.enums:
        for field in msg.fields:
            if enum.name == _get_enum_identifier(field.name):
                # enum name is the same as the field name
                field.type.name = enum.name
                return

        for field in msg.fields:
            if field.type.name == enum.values[0].type.name:
                # enum type is the same as the field type
                field.type.name = msg.name + _get_enum_identifier(field.name)
                enum.name = field.type.name
                return

        if not enum.name or len(msg.enums) == 1:
            enum.name = msg.name + "Type" if msg.fields else msg.name


def _process_comments(instance):
    """Condense comment lines and extract special annotations."""
    lines = instance.annotations
    if not lines:
        return
    # remove empty lines
    lines = [line for line in lines if line]

    instance.annotations = lines

    if (
        not isinstance(instance, FieldDef)
        or instance.type.pkg_name
        or instance.type.name not in PRIMITIVE_TYPES
    ):
        return
    comment = "\n".join(lines)
    match = VALID_REF_COMMENT_PATTERN.search(comment)
    if match:
        # reference to enum
        ref_file_name, ref_common_prefix = match.groups()
        instance.type.name = (
            _get_enum_identifier(
                ref_common_prefix[:-4]
                if ref_common_prefix.endswith("_XXX")
                else ref_common_prefix
            )
            if ref_common_prefix
            else ref_file_name
        )


class MessagePkgDef(BaseMessagePkgDef):
    """Definition of a message package for parsed messages."""

    @classmethod
    def from_msg_folder(cls, package_name: str, msg_pkg_dir: t.Any):
        """Create MessagePkgDef from a folder of .msg files."""
        msg_pkg = cls(package_name, [], [])
        for msg_file in msg_pkg_dir.iterdir():
            if msg_file.suffix == ".msg":
                msg_pkg.messages.append(MessageDef.from_msg_file(msg_file))
            elif msg_file.is_dir():
                msg_pkg.packages.append(
                    cls.from_msg_folder(msg_file.name, msg_file)
                )
        return msg_pkg

    @classmethod
    def from_pkg_folder(cls, root_dir: t.Any, root_dir_name: str = "root"):
        """Create MessagePkgDef from a folder of message folders."""
        out = cls("", [], [])
        for dir in root_dir.rglob("msg"):
            out.packages.append(
                MessagePkgDef.from_msg_folder(
                    dir.parent.name or root_dir_name, dir
                )
            )
        return out
