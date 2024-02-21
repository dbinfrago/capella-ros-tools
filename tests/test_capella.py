# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

import pathlib

import pytest

from capella_ros_tools import capella, messages

EXAMPLE_CAPELLA_PATH = pathlib.Path(__file__).parent.joinpath(
    "data/empty_model"
)


@pytest.fixture
def sample_capella_data_package():
    capella_path = EXAMPLE_CAPELLA_PATH.as_posix()
    return capella.CapellaDataPackage(capella_path, "la")


sample_message_person = messages.MessageDef(
    "Person",
    [
        messages.FieldDef(
            messages.TypeDef(
                "string",
                messages.Range("1", "1"),
            ),
            "name",
            "",
        ),
        messages.FieldDef(
            messages.TypeDef(
                "uint8",
                messages.Range("1", "1"),
                messages.Range("0", "150"),
                None,
            ),
            "age",
            "",
        ),
        messages.FieldDef(
            messages.TypeDef(
                "Pet",
                messages.Range("0", "*"),
            ),
            "pet",
            "",
        ),
    ],
    [],
    "",
)


sample_message_pet = messages.MessageDef(
    "Pet",
    [
        messages.FieldDef(
            messages.TypeDef(
                "string",
                messages.Range("1", "1"),
            ),
            "name",
            "",
        ),
        messages.FieldDef(
            messages.TypeDef(
                "PetType",
                messages.Range("1", "1"),
            ),
            "type",
            "",
        ),
    ],
    [
        messages.EnumDef(
            "PetType",
            [
                messages.ConstantDef(
                    messages.TypeDef(
                        "uint8",
                        messages.Range("1", "1"),
                    ),
                    "CAT",
                    "0",
                    "",
                ),
                messages.ConstantDef(
                    messages.TypeDef("uint8", messages.Range("1", "1")),
                    "DOG",
                    "1",
                    "",
                ),
            ],
            "",
        ),
    ],
    "",
)


@pytest.mark.parametrize(
    "sample_pkg_name", ["test_pkg_name", "test_pkg_name_2"]
)
def test_package(sample_capella_data_package, sample_pkg_name):
    pkg_def = messages.MessagePkgDef(sample_pkg_name, [], [])
    sample_capella_data_package.create_package(
        pkg_def, sample_capella_data_package.data_package
    )

    pkg_obj = sample_capella_data_package.create_package(
        pkg_def, sample_capella_data_package.data_package
    )

    assert pkg_obj in sample_capella_data_package.data_package.packages
    assert pkg_obj.name == sample_pkg_name

    sample_capella_data_package.remove_package(
        pkg_obj, sample_capella_data_package.data_package
    )

    assert pkg_obj not in sample_capella_data_package.data_package.packages


def _create_and_return_class(sample_capella_data_package, sample_message_def):
    sample_capella_data_package.create_class(
        sample_message_def, sample_capella_data_package.data_package
    )
    cls_obj = sample_capella_data_package.create_class(
        sample_message_def, sample_capella_data_package.data_package
    )
    return cls_obj


@pytest.mark.parametrize(
    "sample_message_def", [sample_message_person, sample_message_pet]
)
def test_class(sample_capella_data_package, sample_message_def):
    cls_obj = _create_and_return_class(
        sample_capella_data_package, sample_message_def
    )

    assert cls_obj in sample_capella_data_package.data_package.classes
    assert cls_obj.name == sample_message_def.name

    sample_capella_data_package.remove_class(
        cls_obj, sample_capella_data_package.data_package
    )

    assert cls_obj not in sample_capella_data_package.data_package.classes


def _create_and_return_enum(sample_capella_data_package, sample_enum_def):
    sample_capella_data_package.create_enum(
        sample_enum_def, sample_capella_data_package.data_package
    )
    enum_obj = sample_capella_data_package.create_enum(
        sample_enum_def, sample_capella_data_package.data_package
    )
    return enum_obj


@pytest.mark.parametrize("sample_enum_def", [sample_message_pet.enums[0]])
def test_enum(sample_capella_data_package, sample_enum_def):
    enum_obj = _create_and_return_enum(
        sample_capella_data_package, sample_enum_def
    )

    assert enum_obj in sample_capella_data_package.data_package.datatypes
    assert enum_obj.name == sample_enum_def.name
    assert len(enum_obj.literals) == len(sample_enum_def.literals)
    assert enum_obj.literals[0].name == sample_enum_def.literals[0].name

    sample_capella_data_package.remove_enum(
        enum_obj, sample_capella_data_package.data_package
    )

    assert enum_obj not in sample_capella_data_package.data_package.datatypes


@pytest.mark.parametrize(
    "sample_message_def",
    [sample_message_person, sample_message_pet],
)
def test_create_properties(sample_capella_data_package, sample_message_def):
    cls_obj = _create_and_return_class(
        sample_capella_data_package, sample_message_def
    )
    sample_capella_data_package.create_properties(
        sample_message_def, sample_capella_data_package.data_package
    )

    assert len(cls_obj.owned_properties) == len(sample_message_def.fields)
    for prop, field in zip(
        cls_obj.owned_properties, sample_message_def.fields
    ):
        assert prop.name == field.name

    sample_capella_data_package.remove_class(
        cls_obj, sample_capella_data_package.data_package
    )

    assert not cls_obj in sample_capella_data_package.data_package.classes
