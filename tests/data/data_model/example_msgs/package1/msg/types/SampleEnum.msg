# SPDX-FileCopyrightText: Copyright DB InfraGO AG
# SPDX-License-Identifier: Apache-2.0

# SampleEnum.msg
# This block comment is added to the
# enum description of SampleEnumValue.
uint8 SAMPLE_ENUM_VALUE_RED    = 0
uint8 SAMPLE_ENUM_VALUE_BLUE   = 1  # This inline comment
                                    # is added to the
                                    # enum literal
                                    # description of BLUE.
# This block comment is added to the
# enum literal descriptions of YELLOW and GREEN.
uint8 SAMPLE_ENUM_VALUE_YELLOW = 2
uint8 SAMPLE_ENUM_VALUE_GREEN  = 3

# This block comment is added to the
# enum description of SampleEnum.
# In a file, there can only be one or no enum
# whose literal names do not share a common prefix.
uint8 OK     = 0
uint8 WARN   = 1
uint8 ERROR  = 2

uint8 STALE  = 3
