# SPDX-FileCopyrightText: Copyright DB InfraGO AG
# SPDX-License-Identifier: Apache-2.0

# SampleClass.msg
# The first comment block at the top of the file
# is added to the class description of SampleClass.

# This block comment is added to the
# property description of sample_field1.

# This block comment is also added to the
# property description of sample_field1.
uint8[<=10] sample_field1

# This block comment is added to the property
# descriptions of sample_field2 and sample_field3.
package2/SampleClassEnum[] sample_field2
uint8[3] sample_field3

# This block comment is added to the property
# descriptions of sample_field4 and sample_field5.
uint8 sample_field4  # Fields in SampleClass can reference
                    # enums in other files.
                    # The property sample_field4
                    # is of type SampleEnum.
                    # cf. SampleEnum
uint8 sample_field5     # This inline comment
                        # is added to the
                        # property description of
                        # sample_field5.
                        # The property sample_field5
                        # is of type SampleEnumValue.
                        # cf. SampleEnum, SAMPLE_ENUM_VALUE_XXX
