..
   Copyright DB InfraGO AG and contributors
   SPDX-License-Identifier: Apache-2.0

.. _messages:

*******************
ROS2 Message Layout
*******************

The Capella ROS Tools API expects ROS2 messages to be organized in a specific way:

Class Definition
================
* A `.msg` file can contain one class definition.
* Comments at the top of the file are appended to the class description.
* **Inline Comments:** Comments on the same line as a property definition are directly appended to that property's description.
* **Indented Comment Lines:** Comments on a line of their own but indented are appended to the description of the last encountered property.
* **Block Comments:** Comments on a line of their own and not indented are prepended to the description of the next properties until an empty line or a new block comment is encountered.
* **Unused Comments:** If a block comment has no properties after it before the next empty line or block comment, it is added to the class description itself.

.. code-block:: python

   # MyClass.msg
   # The first comment block at the top of the file
   # is appended to the class description of MyClass.

   # This block comment is appended to the
   # property description of my_field.
   uint8 my_field

   # This block comment is appended to
   # class description of MyClass.

   # This block comment is appended to the property descriptions
   # of my_other_field and my_third_field.
   uint8 my_other_field    # This inline comment
                           # is appended to the
                           # property description of
                           # my_other_field.
   uint8 my_third_field

Enum definition
===============
* A `.msg` file can contain multiple enum definitions.
* Multiple enum definitions are separated by an empty line.
* Enum names are determined based on the longest common prefix of all enum values in the definition.
* If no common prefix exists, the enum name is derived from the file name (excluding the extension).
* Only one or no enum should have value names without a common prefix.
* Comments at the top of the file and unused comments are ignored.
* **Inline Comments:** Comments on the same line as an enum value definition are directly appended to the that enum value's description.
* **Indented Comment Lines:** Comments on a line of their own but indented are appended to the description of the last encountered enum value.
* **Block Comments:** Comments on a line of their own and not indented are appended to the description of the next/current enum definition until an empty line or a new block comment is encountered.

.. code-block:: python

   # MyEnum.msg
   # This block comment is appended to the
   # enum description of MyEnumValue.
   uint8 MY_ENUM_VALUE_RED    = 0
   uint8 MY_ENUM_VALUE_BLUE   = 1   # This inline comment is
                                    # appended to the
                                    # enum value description
                                    # of BLUE.
   # This block comment is also appended to the
   # enum description of MyEnumValue.
   uint8 MY_ENUM_VALUE_YELLOW = 2
   uint8 MY_ENUM_VALUE_GREEN  = 3

   # This block comment is appended to the
   # enum description of MyEnum.
   # In a file, there can only be one or no enum
   # whose value names do not share a common prefix.
   byte OK     = 0
   byte WARN   = 1
   byte ERROR  = 2
   byte STALE  = 3

Enum and Class Definition
=========================
* A `.msg` file can contain one class definition and multiple enum definitions.
* Enums without a common value name prefix are named using the file name plus the suffix "Type."
* There can only be one or no enum whose value names do not share a common prefix.
* Comments at the top of the file are appended to the class description.
* **Inline Comments:** Comments on the same line as a property or enum value are directly appended to the description of that element.
* **Indented Comment Lines:** Comments on a line of their own but indented are appended to the description of the last encountered property or enum value.
* **Block Comments:** Comments on a line of their own and not indented are prepended to the descriptions of the next properties or appended to the descriptions of the next/current enum until an empty line or a new block comment is encountered.
* **Unused Comments:** If a block comment has no following properties or enums before the next empty line or block comment, it is added to the class description.

.. code-block:: python

   # MyMessage.msg
   # The first comment block at the top of the file
   # is appended to the class description of MyMessage.

   uint8 my_field

   # This block comment is appended to the
   # enum description of MyMessageType.
   byte OK     = 0
   byte WARN   = 1
   byte ERROR  = 2
   byte STALE  = 3

Referencing enums
=================

In the Same File
----------------
*  In files that define a class along with enums, the class properties can reference enums defined in the same file. This can be achieved in two ways:

   * **Name Match:** The property name matches the enum name.
   * **Type Match:** The property type matches the enum values type, in which case the updated enum name is derived from the file name plus the property name.

*  Name matching takes precedence over type matching.

.. code-block:: python

   # MyMessage.msg
   # Properties in MyMessage can reference enums in the same file.

   # This block comment is appended to the
   # enum description of MyMessageStatus.
   byte OK     = 0
   byte WARN   = 1
   byte ERROR  = 2
   byte STALE  = 3

   # This block comment is appended to the
   # enum description of Color.
   byte COLOR_RED    = 0
   byte COLOR_BLUE   = 1
   byte COLOR_YELLOW = 2

   byte status  # The property status is of type MyMessageStatus
   byte color    # The property color is of type Color


In another file
---------------
*  If a property definition has a primitive type, it searches for a reference to an enum in the comments and updates the type of the property based on this reference.
*  The reference should follow either of the following formats:

   * **cf. <File Name>:** The enum name is derived from the file name (excluding the extension).
   * **cf. <File Name>, <Common Prefix>_XXX:** The enum name is derived from the longest common prefix of all enum values in the definition.

.. code-block:: python

   # MyEnum.msg
   # This block comment is appended to the
   # enum description of MyEnum.
   byte OK     = 0
   byte WARN   = 1
   byte ERROR  = 2
   byte STALE  = 3

   # This block comment is appended to the
   # enum description of MyEnumValue.
   uint8 MY_ENUM_VALUE_1 = 0
   uint8 MY_ENUM_VALUE_2 = 1
   uint8 MY_ENUM_VALUE_3 = 2

.. code-block:: python

   # MyMessage.msg
   # Fields in MyMessage can reference enums in MyEnum.

   # The property my_enum_field is of type MyEnum
   byte my_enum_field  # cf. MyEnum

   # The property my_other_enum_field is of type MyEnumMyEnumValue
   uint8 my_other_enum_field    # cf. MyEnum, MY_ENUM_VALUE_XXX
