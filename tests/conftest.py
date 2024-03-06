# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

import pytest

from capella_ros_tools.data_model import (
    ConstantDef,
    EnumDef,
    FieldDef,
    MessageDef,
    Range,
    TypeDef,
)


@pytest.fixture
def sample_class_def():
    return MessageDef(
        name="SampleClass",
        fields=[
            FieldDef(
                type=TypeDef("uint8", Range("1", "1"), Range("0", "10"), None),
                name="sample_field1",
                description="<p>This block comment is added to the</p>"
                "<p>property description of sample_field1.</p>"
                "<p>This block comment is also added to the</p>"
                "<p>property description of sample_field1.</p>",
            ),
            FieldDef(
                type=TypeDef("uint8", Range("1", "1"), None, None),
                name="sample_field2",
                description="<p>This block comment is added to the property</p>"
                "<p>descriptions of sample_field2 and sample_field3.</p>",
            ),
            FieldDef(
                TypeDef("uint8", Range("0", "*"), None, None),
                name="sample_field3",
                description="<p>This block comment is added to the property</p>"
                "<p>descriptions of sample_field2 and sample_field3.</p>",
            ),
            FieldDef(
                type=TypeDef("SampleEnum", Range("1", "1"), None, "types"),
                name="sample_field4",
                description="<p>This block comment is added to the property</p>"
                "<p>descriptions of sample_field4 and sample_field5.</p>"
                "<p>Fields in SampleClass can reference</p>"
                "<p>enums in other files.</p>"
                "<p>The property sample_field4</p>"
                "<p>is of type SampleEnum.</p>"
                "<p>cf. SampleEnum</p>",
            ),
            FieldDef(
                type=TypeDef(
                    "SampleEnumValue", Range("1", "1"), None, "types"
                ),
                name="sample_field5",
                description="<p>This block comment is added to the property</p>"
                "<p>descriptions of sample_field4 and sample_field5.</p>"
                "<p>This inline comment</p>"
                "<p>is added to the</p>"
                "<p>property description of</p>"
                "<p>sample_field5.</p>"
                "<p>The property sample_field5</p>"
                "<p>is of type SampleEnumValue.</p>"
                "<p>cf. SampleEnum, SAMPLE_ENUM_VALUE_XXX</p>",
            ),
        ],
        enums=[],
        description="<p>SampleClass.msg</p>"
        "<p>The first comment block at the top of the file</p>"
        "<p>is added to the class description of SampleClass.</p>",
    )


@pytest.fixture
def sample_enum_def():
    return MessageDef(
        name="SampleEnum",
        fields=[],
        enums=[
            EnumDef(
                name="SampleEnumValue",
                literals=[
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="RED",
                        value="0",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="BLUE",
                        value="1",
                        description="<p>This inline comment</p>"
                        "<p>is added to the</p>"
                        "<p>enum literal</p>"
                        "<p>description of BLUE.</p>",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="YELLOW",
                        value="2",
                        description="<p>This block comment is added to the</p>"
                        "<p>enum literal descriptions of YELLOW and GREEN.</p>",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="GREEN",
                        value="3",
                        description="<p>This block comment is added to the</p>"
                        "<p>enum literal descriptions of YELLOW and GREEN.</p>",
                    ),
                ],
                description="<p>SampleEnum.msg</p>"
                "<p>This block comment is added to the</p>"
                "<p>enum description of SampleEnumValue.</p>",
            ),
            EnumDef(
                name="SampleEnum",
                literals=[
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="OK",
                        value="0",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="WARN",
                        value="1",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="ERROR",
                        value="2",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="STALE",
                        value="3",
                        description="",
                    ),
                ],
                description="<p>This block comment is added to the</p>"
                "<p>enum description of SampleEnum.</p>"
                "<p>In a file, there can only be one or no enum</p>"
                "<p>whose literal names do not share a common prefix.</p>",
            ),
        ],
        description="",
    )


@pytest.fixture
def sample_class_enum_def():
    return MessageDef(
        name="SampleClassEnum",
        fields=[
            FieldDef(
                type=TypeDef(
                    "SampleClassEnumStatus", Range("1", "1"), None, "types"
                ),
                name="status",
                description="<p>The property status is of type</p>"
                "<p>SampleClassEnumStatus.</p>",
            ),
            FieldDef(
                type=TypeDef("Color", Range("1", "1"), None, "types"),
                name="color",
                description="<p>The property color is of type Color.</p>",
            ),
            FieldDef(
                type=TypeDef("uint8", Range("1", "1"), None, None),
                name="field",
                description="",
            ),
        ],
        enums=[
            EnumDef(
                name="SampleClassEnumStatus",
                literals=[
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="OK",
                        value="0",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="WARN",
                        value="1",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="ERROR",
                        value="2",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="STALE",
                        value="3",
                        description="",
                    ),
                ],
                description="<p>This block comment is added to the</p>"
                "<p>enum description of SampleClassEnumStatus.</p>",
            ),
            EnumDef(
                name="Color",
                literals=[
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="RED",
                        value="0",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="BLUE",
                        value="1",
                        description="",
                    ),
                    ConstantDef(
                        type=TypeDef("uint8", Range("1", "1"), None, None),
                        name="YELLOW",
                        value="2",
                        description="",
                    ),
                ],
                description="<p>This block comment is added to the</p>"
                "<p>enum description of Color.</p>",
            ),
        ],
        description="<p>SampleClassEnum.msg</p>"
        "<p>Properties in SampleClassEnum can reference</p>"
        "<p>enums in the same file.</p>",
    )
