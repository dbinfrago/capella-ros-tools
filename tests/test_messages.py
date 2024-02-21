# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest

from capella_ros_tools.messages import (
    CONSTANT_SEPARATOR,
    UPPER_BOUND_TOKEN,
    ConstantDef,
    FieldDef,
    MessageDef,
    MessagePkgDef,
    Range,
    TypeDef,
)

PATH = Path(__file__).parent


@pytest.mark.parametrize(
    "params, expected_output",
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
    ],
)
def test_TypeDef_str(params, expected_output):
    name, card, range, package = params

    type_def = TypeDef(name, card, range, package)

    assert str(type_def) == expected_output


@pytest.mark.parametrize(
    "type_str, expected_output",
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
    ],
)
def test_TypeDef_from_string(type_str, expected_output):
    name, card, range, package = expected_output
    type_def = TypeDef.from_string(type_str)

    assert type_def.name == name
    assert type_def.card == card
    assert type_def.range == range
    assert type_def.package == package


@pytest.mark.parametrize(
    "params, expected_output",
    [
        (
            ("test_type", "test_name", "test_description"),
            "test_type test_name    # test_description",
        ),
    ],
)
def test_FieldDef_str(params, expected_output):
    type_str, name, description = params
    type_def = TypeDef.from_string(type_str)

    field_def = FieldDef(type_def, name, description)

    assert str(field_def) == expected_output


@pytest.mark.parametrize(
    "params, expected_output",
    [
        (
            ("test_type", "test_name", 1, "test_description"),
            f"test_type test_name {CONSTANT_SEPARATOR} 1    # test_description",
        ),
    ],
)
def test_ConstantDef_str(params, expected_output):
    type_str, name, value, description = params
    type_def = TypeDef.from_string(type_str)

    constant_def = ConstantDef(type_def, name, value, description)

    assert str(constant_def) == expected_output


@pytest.mark.parametrize(
    "msg_file_path",
    [
        PATH.joinpath("data/example_msgs/msg/CameraInfo.msg"),
        PATH.joinpath("data/example_msgs/msg/DiagnosticStatus.msg"),
        PATH.joinpath("data/example_msgs/msg/PointCloud2.msg"),
    ],
)
def test_MessageDef(msg_file_path):
    message_def = MessageDef.from_file(msg_file_path)

    assert message_def.name == msg_file_path.stem
    assert str(message_def) == msg_file_path.read_text()


@pytest.mark.parametrize(
    "pkg_name, msg_path",
    [
        ("example_msgs", PATH.joinpath("data/example_msgs")),
    ],
)
def test_MessagePkgDef_from_msg_folder(pkg_name, msg_path):
    message_pkg_def = MessagePkgDef.from_msg_folder(pkg_name, msg_path)

    assert message_pkg_def.name == pkg_name
    assert len(message_pkg_def.messages) == len(list(msg_path.rglob("*.msg")))
