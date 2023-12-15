# Copyright DB Netz AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""IDL Message definition.""" ""
import typing as t


class BaseTypeDef:
    """Type definition for a field or constant in a message."""

    def __init__(
        self,
        name: str,
        array_size: float | None = None,
        pkg_name: str | None = None,
    ) -> None:
        self.name = name
        """Name of the type."""
        self.array_size = array_size
        """Max size of the array."""
        self.pkg_name = pkg_name
        """Name of the package the type is defined in.

        None:   type is a primitive type or
                defined in the same package as the message
        """


class FieldDef:
    """Definition of a field."""

    def __init__(self, type: t.Any, name: str, annotations: list[str]) -> None:
        self.type = type
        self.name = name
        self.annotations = annotations


class ConstantDef:
    """Definition of a constant."""

    def __init__(
        self,
        type: t.Any,
        name: str,
        value: str,
        annotations: list[str],
    ) -> None:
        self.type = type
        self.name = name
        self.value = value
        self.annotations = annotations


class EnumDef:
    """Definition of an enum."""

    def __init__(
        self, name: str, values: list[ConstantDef], annotations: list[str]
    ) -> None:
        self.name = name
        self.values = values
        self.annotations = annotations


class BaseMessageDef:
    """Definition of a message."""

    def __init__(
        self,
        name: str,
        fields: list[FieldDef],
        enums: list[EnumDef],
        annotations: list[str],
    ) -> None:
        self.name = name
        self.fields = fields
        self.enums = enums
        self.annotations = annotations

    def _repr_html_(self):
        fragments = []
        fragments.append(
            f"<h1>{self.name}</h1><p>"
            + "<br>".join(self.annotations)
            + "</p><h2>Fields</h2><ol>"
        )
        for field in self.fields:
            fragments.append(
                f'<li>{field.type.pkg_name+"/" if field.type.pkg_name else ""}{field.type.name}{"[]" if field.type.array_size == float("inf") else f"[{field.type.array_size}]" if field.type.array_size else ""} {field.name}<br>'
                + "<br>".join(field.annotations)
                + "</li>"
            )
        fragments.append("</ol><h2>Enums</h2><ol>")
        for enum in self.enums:
            fragments.append(
                f"<li><b>{enum.name}</b><br>"
                + "<br>".join(enum.annotations)
                + "<ul>"
            )
            for value in enum.values:
                fragments.append(
                    f"<li>{value.type.name} {value.name} = {value.value}<br>"
                    + "<br>".join(value.annotations)
                    + "</li>"
                )
            fragments.append("</ul></li>")
        fragments.append("</ol>")

        return "".join(fragments)


class BaseMessagePkgDef:
    """Definition of a message package."""

    def __init__(self, name: str, messages: list, packages: list):
        self.name = name
        self.messages = messages
        self.packages = packages

    def _repr_html_(self):
        return f'<h1>{self.name}</h1><h2>Messages</h2><ol>{"".join([f"<li>{msg.name}</li>" for msg in self.messages])}</ol><h2>Packages</h2><ol>{"".join([f"<li>{pkg.name}</li>" for pkg in self.packages])}</ol>'
