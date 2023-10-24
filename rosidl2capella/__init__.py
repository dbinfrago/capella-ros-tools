# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""The rosidl2capella package."""
from importlib import metadata

try:
    __version__ = metadata.version("rosidl2capella")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"
del metadata
