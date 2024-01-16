..
   Copyright DB InfraGO AG and contributors
   SPDX-License-Identifier: Apache-2.0

.. _messages:

*******************
ROS2 Message Layout
*******************

The Capella ROS Tools API expects ROS2 messages to be organized in a specific way:

Class definition
=================
.. code-block:: python
   :linenos:

   # MyClass.msg
   # The first comment block at the top of the file
   # is appended to the class description of MyClass.

   # This block comment is appended to the
   # property description of my_field.
   uint8 my_field

   # This block comment is appended to
   # class description of MyClass.

   # This block comment is appended to the
   # property description of my_other_field.
   uint8 my_other_field     # This inline comment
                            # is appended to the
                            # property description of
                            # my_other_field.

   uint8 my_third_field

Enum definition
===============
.. code-block:: python
   :linenos:

   # MyEnum.msg
   # This block comment is appended to the
   # enum description of MyEnumMyEnumValue.
   uint8 MY_ENUM_VALUE_RED = 0
   uint8 MY_ENUM_VALUE_BLUE = 1    # This inline comment is
                                   # appended to the
                                   # enum value description
                                   # of BLUE.
   uint8 MY_ENUM_VALUE_YELLOW = 2

   # This block comment is appended to the
   # enum description of MyEnum.
   # In a file, there can only be one or no enum
   # whose value names do not share a common prefix.
   byte OK     = 0
   byte WARN   = 1
   byte ERROR  = 2
   byte STALE  = 3

Enum and class definition
=========================
.. code-block:: python
   :linenos:

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

In the same file
----------------
.. code-block:: python
   :linenos:

   # MyMessage.msg
   # Fields in MyMessage can reference enums in the same file.

   # This block comment is appended to the
   # enum description of MyMessageType.
   byte OK     = 0
   byte WARN   = 1
   byte ERROR  = 2
   byte STALE  = 3

   # This block comment is appended to the
   # enum description of MyMessageColor.
   byte COLOR_RED     = 0
   byte COLOR_BLUE   = 1
   byte COLOR_YELLOW  = 2

   byte my_field  # The property my_field is of type MyMessageType
   uint8 color    # The property color is of type MyMessageColor


In another file
---------------
.. code-block:: python
   :linenos:

   # MyEnum.msg
   # This block comment is appended to the
   # enum description of MyEnum.
   byte OK     = 0
   byte WARN   = 1
   byte ERROR  = 2
   byte STALE  = 3

   # This block comment is appended to the
   # enum description of MyEnumMyEnumValue.
   uint8 MY_ENUM_VALUE_1 = 0
   uint8 MY_ENUM_VALUE_2 = 1
   uint8 MY_ENUM_VALUE_3 = 2

.. code-block:: python
   :linenos:

   # MyMessage.msg
   # Fields in MyMessage can reference enums in MyEnum.

   # The property my_enum_field is of type MyEnum
   byte my_enum_field  # cf. MyEnum

   # The property my_other_enum_field is of type MyEnumMyEnumValue
   uint8 my_other_enum_field    # cf. MyEnum, MY_ENUM_VALUE_XXX
