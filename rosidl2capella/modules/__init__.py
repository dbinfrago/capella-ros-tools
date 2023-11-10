# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""The capella ros-tools modules package."""
from collections import namedtuple

import capellambse

ROS_INTERFACES = "ros_interfaces"
BASIC_TYPES = "basic_types"


EnumValue = namedtuple("EnumValue", ["name", "type", "value", "comment"])
MsgProp = namedtuple(
    "MsgProp", ["name", "type", "typedir", "min", "max", "comment"]
)


class BaseCapella:
    """Base class for capella model."""

    def __init__(
        self,
        path_to_capella_model: str,
        layer: str,
    ) -> None:
        self.model = capellambse.MelodyModel(path_to_capella_model)
        self.data = getattr(self.model, layer).data_package


class MessageDef:
    """Message definition."""

    def __init__(self, name: str, description: str, props: list):
        self.name = name
        self.description = description
        self.props = props


class MessagesPkg:
    """Messages package."""

    def __init__(self, messages: dict, packages: dict):
        self.messages = messages
        self.packages = packages
