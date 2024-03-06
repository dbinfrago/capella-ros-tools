# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

import pathlib

import pytest
from capellambse.filehandler import abc

from capella_ros_tools import data_model
from capella_ros_tools.data_model import (
    CONSTANT_SEPARATOR,
    UPPER_BOUND_TOKEN,
    ConstantDef,
    EnumDef,
    FieldDef,
    MessageDef,
    MessagePkgDef,
    Range,
    TypeDef,
)

PATH = pathlib.Path(__file__).parent

SAMPLE_CLASS_PATH = PATH.joinpath(
    "data/data_model/example_msgs/package1/msg/SampleClass.msg"
)
SAMPLE_ENUM_PATH = PATH.joinpath(
    "data/data_model/example_msgs/package1/msg/SampleEnum.msg"
)
SAMPLE_CLASS_ENUM_PATH = PATH.joinpath(
    "data/data_model/example_msgs/package2/msg/SampleClassEnum.msg"
)

PACKAGE1_PATH = PATH.joinpath("data/data_model/example_msgs/package1")
PACKAGE2_PATH = PATH.joinpath("data/data_model/example_msgs/package2")


@pytest.mark.parametrize(
    "params, expected",
    [
        (
            ("test_name", Range("1", "1"), None, "test_package"),
            "test_package/test_name",
        ),
        (
            ("test_name", Range("0", "10"), None, "test_package"),
            "test_package/test_name[10]",
        ),
        (
            ("test_name", Range("1", "1"), Range("0", "10"), "test_package"),
            f"test_package/test_name[{UPPER_BOUND_TOKEN}10]",
        ),
        (
            ("test_name", Range("1", "1"), None, None),
            "test_name",
        ),
        (
            ("test_name", Range("0", "*"), None, None),
            "test_name[]",
        ),
    ],
)
def test_TypeDef_str(
    params: tuple[str, Range, Range | None, str | None], expected: str
):
    type_def = TypeDef(*params)

    assert str(type_def) == expected


@pytest.mark.parametrize(
    "type_str, params",
    [
        (
            "test_package/test_name",
            ("test_name", Range("1", "1"), None, "test_package"),
        ),
        (
            "test_package/test_name[10]",
            ("test_name", Range("0", "10"), None, "test_package"),
        ),
        (
            f"test_package/test_name[{UPPER_BOUND_TOKEN}10]",
            ("test_name", Range("1", "1"), Range("0", "10"), "test_package"),
        ),
        (
            "test_name[]",
            ("test_name", Range("0", "*"), None, None),
        ),
    ],
)
def test_TypeDef_from_string(
    type_str: str, params: tuple[str, Range, Range | None, str | None]
):
    type_def = TypeDef.from_string(type_str)
    expected = TypeDef(*params)

    assert type_def == expected


@pytest.mark.parametrize(
    "params, expected",
    [
        (
            (
                TypeDef.from_string("test_type"),
                "test_name",
                "test_description",
            ),
            "test_type test_name    # test_description",
        ),
        (
            (TypeDef.from_string("test_type"), "test_name", ""),
            "test_type test_name",
        ),
    ],
)
def test_FieldDef_str(params: tuple[TypeDef, str, str], expected: str):
    field_def = FieldDef(*params)

    assert str(field_def) == expected


@pytest.mark.parametrize(
    "params, expected",
    [
        (
            (
                TypeDef.from_string("test_type"),
                "test_name",
                "1",
                "test",
            ),
            f"test_type test_name {CONSTANT_SEPARATOR} 1    # test",
        ),
        (
            (TypeDef.from_string("test_type"), "test_name", "10", ""),
            f"test_type test_name {CONSTANT_SEPARATOR} 10",
        ),
    ],
)
def test_ConstantDef_str(params: tuple[TypeDef, str, str, str], expected: str):
    constant_def = ConstantDef(*params)

    assert str(constant_def) == expected


def test_extract_file_level_comments_no_comments():
    msg_string = """uint8 OK = 0
uint8 WARN = 1
uint8 ERROR = 2"""
    comments, _ = data_model._extract_file_level_comments(msg_string)

    assert comments == ""


def test_extract_file_level_comments_no_newline():
    msg_string = """# This is a comment
# This is another comment
uint8 OK = 0
uint8 WARN = 1
uint8 ERROR = 2"""
    comments, _ = data_model._extract_file_level_comments(msg_string)

    assert comments == ""


def test_extract_file_level_comments():
    msg_string = """# This is a comment
# This is another comment

uint8 OK = 0
uint8 WARN = 1
uint8 ERROR = 2"""
    comments, _ = data_model._extract_file_level_comments(msg_string)
    expected = "<p>This is a comment</p><p>This is another comment</p>"

    assert comments == expected


class TestEnumDef:
    @staticmethod
    @pytest.fixture
    def expected():
        type_def = TypeDef("uint8", Range("1", "1"))
        enum_def = EnumDef(
            name="enum_name",
            literals=[
                ConstantDef(
                    type=type_def,
                    name="OK",
                    value="0",
                    description="",
                ),
                ConstantDef(
                    type=type_def,
                    name="WARN",
                    value="1",
                    description="",
                ),
                ConstantDef(
                    type=type_def,
                    name="ERROR",
                    value="2",
                    description="",
                ),
                ConstantDef(
                    type=type_def,
                    name="STALE",
                    value="3",
                    description="",
                ),
            ],
            description="",
        )
        return MessageDef("enum_name", [], [enum_def], "")

    @staticmethod
    def test_merge_enums_before(expected):

        msg_string = """
uint8 OK = 0

uint8 WARN = 1
uint8 ERROR = 2
uint8 STALE = 3
"""
        msg_def = MessageDef.from_string("enum_name", msg_string)
        assert msg_def == expected

    @staticmethod
    def test_merge_enums_after(expected):
        msg_string = """
uint8 OK = 0
uint8 WARN = 1
uint8 ERROR = 2

uint8 STALE = 3
        """
        msg_def = MessageDef.from_string("enum_name", msg_string)
        assert msg_def == expected

    @staticmethod
    def test_merge_enums_multiple_after(expected):
        msg_string = """
uint8 OK = 0
uint8 WARN = 1

uint8 ERROR = 2

uint8 STALE = 3
        """
        msg_def = MessageDef.from_string("enum_name", msg_string)
        assert msg_def == expected

    @staticmethod
    def test_merge_enums_multiple_before(expected):
        msg_string = """
uint8 OK = 0

uint8 WARN = 1

uint8 ERROR = 2
uint8 STALE = 3
        """
        msg_def = MessageDef.from_string("enum_name", msg_string)
        assert msg_def == expected


def test_MessageDef_class(sample_class_def):
    msg_path = SAMPLE_CLASS_PATH
    msg_def = MessageDef.from_file(msg_path)
    expected = sample_class_def
    assert msg_def == expected


def test_MessageDef_enum(sample_enum_def):
    msg_path = SAMPLE_ENUM_PATH
    msg_def = MessageDef.from_file(msg_path)
    expected = sample_enum_def
    assert msg_def == expected


def test_MessageDef_class_enum(sample_class_enum_def):
    msg_path = SAMPLE_CLASS_ENUM_PATH
    msg_def = MessageDef.from_file(msg_path)
    expected = sample_class_enum_def
    assert msg_def == expected


@pytest.mark.parametrize(
    "msg_pkg_path",
    [
        PACKAGE1_PATH,
        PACKAGE2_PATH,
    ],
)
def test_MessagePkgDef_from_msg_folder(
    msg_pkg_path: abc.AbstractFilePat | pathlib.Path,
):
    message_pkg_def = MessagePkgDef.from_msg_folder("", msg_pkg_path)

    assert message_pkg_def.messages
