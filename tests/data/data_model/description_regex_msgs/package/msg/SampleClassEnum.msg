# SPDX-FileCopyrightText: Copyright DB InfraGO AG
# SPDX-License-Identifier: Apache-2.0

# Decision
#
# Created:  2023-08-29
# Modified: 2023-08-29
# Version:  0.1
# Status:   Draft
#
# Description: Message type for providing the made decision.
# An additional description line.
#
# Expect linebreak

# This block comment is added to the
# enum description of SampleClassEnumStatus.
uint8 OK     = 0
uint8 WARN   = 1
uint8 ERROR  = 2
uint8 STALE  = 3

# This block comment is added to the
# enum description of Color.
uint8 COLOR_RED    = 0
uint8 COLOR_BLUE   = 1
uint8 COLOR_YELLOW = 2

uint8 status    # The property status is of type
                # SampleClassEnumStatus.
uint8 color   # The property color is of type Color.
uint8 field
