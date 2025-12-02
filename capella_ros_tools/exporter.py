# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0
"""Tool for exporting a Capella data package to ROS messages."""

import collections
import dataclasses
import itertools
import pathlib
import re
import typing as t
from html import parser

import capellambse
import jinja2
import pydantic
import yaml
from capellambse.metamodel import information

from . import logger

PACKAGE_XML = "package.xml"
C_MAKE_LISTS_TXT = "CMakeLists.txt"
GENERIC_PKG_NAME = "generic"
UNKNOWN_TYPE = "unknown"
DEFAULT_ENUM_TYPE = "int32"
PACKAGE_PATH = "export_templates"
ROS_TYPES = [
    "bool",
    "byte",
    "char",
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
    "float32",
    "float64",
    "string",
]
INT_LENGTHS = [8, 16, 32, 64]
FLOAT_LENGTHS = [32, 64]

UINT_REGEX = re.compile(r"^uint(\d+)")
INT_REGEX = re.compile(r"^int(\d+)")
FLOAT_REGEX = re.compile(r"^float(\d+)")


class RosExportHelper:
    @staticmethod
    def int_bytes(length: int) -> int:
        """Return ROS byte length for integers."""
        for int_length in INT_LENGTHS:
            if length <= int_length:
                return int_length
        raise ValueError(f"Invalid integer length {length}")

    @staticmethod
    def float_bytes(length: int) -> int:
        """Return ROS byte length for floats."""
        for float_length in FLOAT_LENGTHS:
            if length <= float_length:
                return float_length
        raise ValueError(f"Invalid float length {length}")

    @staticmethod
    def make_doc_str(markup: str) -> list[str]:
        _parser = LineSeparationHTMLParser()
        _parser.feed(markup)

        return _parser.text_list

    @staticmethod
    def make_snake_case(name: str) -> str:
        """Convert all cases to snake_case."""
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = name.lower()
        # Replace invalid characters with underscores
        name = re.sub("[^a-z0-9_]", "_", name)
        name = re.sub("^[^a-z]+", "", name)
        name = re.sub("_+", "_", name)
        return re.sub("_$", "", name)

    @staticmethod
    def make_camel_case(name: str) -> str:
        """Convert all cases to CamelCase."""
        temp_parts = re.split(r"[^a-zA-Z0-9]+", name)
        parts = []
        for part in temp_parts:
            if not part:
                continue
            parts.extend(re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", part))

        words = [word for word in parts if word]

        camel_case_name = "".join(
            w if w.isdigit() else w.capitalize() for w in words
        )

        if not camel_case_name or not camel_case_name[0].isalpha():
            camel_case_name = "A" + camel_case_name

        return camel_case_name

    @staticmethod
    def type_name_for_datatype(
        dt: information.datatype.DataType, custom_types: dict[str, str]
    ) -> str:
        """Create type name from data type."""
        name = dt.name
        if ros := custom_types.get(name):
            return ros
        if name in ROS_TYPES:
            return name
        if m := UINT_REGEX.match(name):
            return f"uint{RosExportHelper.int_bytes(int(m.group(1)))}"
        if m := INT_REGEX.match(name):
            return f"int{RosExportHelper.int_bytes(int(m.group(1)))}"
        if m := FLOAT_REGEX.match(name):
            return f"float{RosExportHelper.float_bytes(int(m.group(1)))}"
        logger.error("Type %s is unknown.", name)
        return name

    @staticmethod
    def apply_cardinality(prop: information.Property, base_type: str) -> str:
        """Add cardinality to an existing property name."""
        try:
            min_c, max_c = prop.min_card.value, prop.max_card.value
        except AttributeError:
            return base_type
        if (min_c, max_c) == ("1", "1"):
            return base_type
        if max_c == "*":
            return f"{base_type}[]"
        if min_c == max_c:
            return f"{base_type}[{min_c}]"
        return f"{base_type}[<={max_c}]"


class ExporterConfig(pydantic.BaseModel):
    """Config for a customized exporter."""

    packages: dict[str, str]
    built_ins: dict[str, str]
    custom_packages: dict[str, list[str]]
    custom_types: dict[str, str]
    contact_email: str = "dummy@dummy"
    maintainer: str = "Dummy Company"
    project_name: str = "custom_ros_msgs"
    pkg_postfix: str = ""


def load_config(
    config: pathlib.Path, model: capellambse.MelodyModel | None = None
) -> ExporterConfig:
    """Load the given config file and render jinja, if needed."""
    if config.name.endswith(".j2"):
        assert model is not None, "For jinja configs the model is mandatory"
        template = jinja2.Template(config.read_text("utf-8"))
        content = yaml.safe_load(template.render(model=model))
    else:
        content = yaml.safe_load(config.read_text("utf-8"))
    return ExporterConfig(**content)


def topological_sort(
    dependencies: t.Mapping[str, t.Iterable[str]],
) -> list[str]:
    """Sort the packages in a way that dependencies are listed first."""
    # Create an adjacency list and count of in-degrees
    adj_list: collections.defaultdict[str, set[str]] = collections.defaultdict(
        set
    )
    in_degrees: collections.defaultdict[str, int] = collections.defaultdict(
        int
    )

    # Initialize the adjacency list and in-degrees count correctly
    for package, deps in dependencies.items():
        for dep in deps:
            if dep in dependencies:  # Only consider relevant dependencies
                adj_list[dep].add(package)
                in_degrees[package] += 1

    # Ensure all packages are in the in-degree dictionary
    for package in dependencies:
        if package not in in_degrees:
            in_degrees[package] = 0

    # Find all packages with no incoming edges
    zero_in_degree = collections.deque(
        [pkg for pkg, degree in in_degrees.items() if degree == 0]
    )

    sorted_packages: list[str] = []
    while zero_in_degree:
        package = zero_in_degree.popleft()
        sorted_packages.append(package)

        for neighbor in adj_list[package]:
            in_degrees[neighbor] -= 1
            if in_degrees[neighbor] == 0:
                zero_in_degree.append(neighbor)

    # Check for circular dependencies
    if len(sorted_packages) != len(dependencies):
        logger.error("Circular dependency detected!")
        # On best effort basis, add the remaining packages.
        remaining_packages = set(dependencies.keys()) - set(sorted_packages)
        sorted_packages.extend(remaining_packages)

    return sorted_packages


@dataclasses.dataclass
class LiteralData:
    """Data for class properties and enum values."""

    type: str
    name: str
    value: str | None = None
    docstr: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class ClassData:
    """Data for a class."""

    name: str
    docstr: list[str] = dataclasses.field(default_factory=list)
    literals: list[LiteralData] = dataclasses.field(default_factory=list)


class LineSeparationHTMLParser(parser.HTMLParser):
    """An HTML parser to convert an HTML string to a list of plain strings."""

    def __init__(self) -> None:
        super().__init__()
        self.text_list: list[str] = []

    def handle_data(self, data: str) -> None:
        """Process data and fill the text list."""
        if data.strip():  # Skipping empty strings
            self.text_list.append(data.strip())


class Exporter:
    """Simplified exporter: prepares data on init, exports ROS pkgs."""

    data_packages: dict[str, list[ClassData]]
    dependencies: dict[str, set[str]]

    def __init__(
        self,
        packages: dict[str, str],
        built_ins: dict[str, str],
        custom_pkg: dict[str, list[str]],
        custom_types: dict[str, str],
        model: capellambse.MelodyModel,
        generate_cmake: bool,  # noqa: FBT001
        pkg_postfix: str | None = None,
    ) -> None:
        self.generate_cmake = generate_cmake
        self.pkg_postfix = pkg_postfix or ""
        self.jinja_env = jinja2.Environment(
            loader=jinja2.PackageLoader(
                __name__.rsplit(".", 1)[0], PACKAGE_PATH
            )
        )
        self.data_packages, self.dependencies = self._prepare(
            packages, built_ins, custom_pkg, custom_types, model
        )

    # ---------- Preparation ----------

    def _prepare(
        self,
        packages: dict[str, str],
        built_ins: dict[str, str],
        custom_pkg: dict[str, list[str]],
        custom_types: dict[str, str],
        model: capellambse.MelodyModel,
    ) -> tuple[dict[str, list[ClassData]], dict[str, set[str]]]:
        stop_uuids = set(packages.values()) | set(built_ins.values())
        resolved_custom = {
            p: [model.by_uuid(u) for u in uuids]
            for p, uuids in custom_pkg.items()
        }

        # Collect built-in map and per-package classes
        class_to_pkg: dict[str, str] = {}
        package_classes: dict[str, list[information.Class]] = {}
        for pkg_name, uuid in built_ins.items():
            classes = self._walk_classes(model.by_uuid(uuid), stop_uuids)
            for c in classes:
                class_to_pkg[c.uuid] = pkg_name
        for pkg_name, uuid in packages.items():
            package_classes[pkg_name] = self._walk_classes(
                model.by_uuid(uuid), stop_uuids
            )
        for pkg_name, classes in resolved_custom.items():
            package_classes[pkg_name] = [
                c for c in classes if c.uuid not in class_to_pkg
            ]  # exclude built-ins

        # Extend class_to_pkg with all package classes
        for pkg_name, classes in package_classes.items():
            for c in classes:
                class_to_pkg[c.uuid] = pkg_name

        deps_by_pkg, multi_dep, dup_ids = self._collect_all_deps(
            package_classes, class_to_pkg
        )
        messages_by_pkg: dict[str, list[ClassData]] = {}
        pkg_deps: dict[str, set[str]] = {}

        # Generic package for multiply referenced deps
        if multi_dep:
            generic = GENERIC_PKG_NAME
            pkg_deps[generic] = set()
            messages_by_pkg[generic] = [
                self._build_class_data(
                    c,
                    generic,
                    class_to_pkg,
                    dup_ids,
                    pkg_deps[generic],
                    custom_types,
                    built_ins,
                )
                for c in multi_dep
            ]
            for c in multi_dep:
                class_to_pkg[c.uuid] = generic
            deps_by_pkg = {
                pkg: [c for c in classes if c.uuid not in dup_ids]
                for pkg, classes in deps_by_pkg.items()
            }

        for pkg_name, classes in package_classes.items():
            pkg_deps[pkg_name] = set()
            all_cls_uuids = [
                c.uuid
                for c in itertools.chain(
                    classes, deps_by_pkg.get(pkg_name, [])
                )
            ]
            seen: set[str] = set()
            bucket: list[ClassData] = []
            for c in itertools.chain(classes, deps_by_pkg.get(pkg_name, [])):
                if c.uuid in seen:
                    continue
                seen.add(c.uuid)
                bucket.append(
                    self._build_class_data(
                        c,
                        pkg_name,
                        class_to_pkg,
                        all_cls_uuids,
                        pkg_deps[pkg_name],
                        custom_types,
                        built_ins,
                    )
                )
            messages_by_pkg[pkg_name] = bucket

        return messages_by_pkg, pkg_deps

    def _walk_classes(
        self,
        pkg: information.DataPkg,
        stop_uuids: set[str],
        out: list[information.Class] | None = None,
    ) -> list[information.Class]:
        out = list(pkg.classes) if out is None else (out + list(pkg.classes))
        for sub in pkg.packages:
            if sub.uuid not in stop_uuids:
                self._walk_classes(sub, stop_uuids, out)
        return out

    def _collect_cls_deps(
        self,
        cls: information.Class,
        class_to_pkg: dict[str, str],
        bucket: list[information.Class],
    ) -> None:
        for prop in cls.properties:
            _type = prop.type
            if isinstance(_type, information.Class):
                if _type.uuid in class_to_pkg or _type in bucket:
                    continue
                bucket.append(_type)
                self._collect_cls_deps(_type, class_to_pkg, bucket)

    def _collect_all_deps(
        self,
        package_classes: t.Mapping[str, t.Iterable[information.Class]],
        class_to_pkg: dict[str, str],
    ) -> tuple[
        dict[str, list[information.Class]], list[information.Class], set[str]
    ]:
        deps: dict[str, list[information.Class]] = {}
        seen: set[str] = set()
        dup_ids: set[str] = set()
        multi: list[information.Class] = []
        for pkg, classes in package_classes.items():
            bucket: list[information.Class] = []
            for c in classes:
                self._collect_cls_deps(c, class_to_pkg, bucket)
            deps[pkg] = bucket
            for c in bucket:
                if c.uuid in seen and c.uuid not in dup_ids:
                    dup_ids.add(c.uuid)
                    multi.append(c)
                else:
                    seen.add(c.uuid)
        return deps, multi, dup_ids

    # ---------- Class and type handling ----------

    def _build_class_data(
        self,
        cls: information.Class,
        current_pkg: str,
        class_to_pkg: dict[str, str],
        pkg_cls_uuids: t.Iterable[str],
        pkg_deps: set[str],
        custom_types: dict[str, str],
        built_ins: dict[str, str],
    ) -> ClassData:
        data = ClassData(
            RosExportHelper.make_camel_case(cls.name),
            RosExportHelper.make_doc_str(cls.description),
        )
        for prop in cls.properties:
            prop_name = RosExportHelper.make_snake_case(prop.name)
            base_type = self._prop_type_name(
                prop.type,
                class_to_pkg,
                cls,
                data,
                current_pkg,
                pkg_cls_uuids,
                pkg_deps,
                prop_name,
                custom_types,
                built_ins,
            )
            full_type = RosExportHelper.apply_cardinality(prop, base_type)
            data.literals.append(
                LiteralData(
                    full_type,
                    prop_name,
                    docstr=RosExportHelper.make_doc_str(prop.description),
                )
            )
        return data

    def _prop_type_name(
        self,
        prop_type: capellambse.model.ModelElement,
        class_to_pkg: dict[str, str],
        ctx_cls: information.Class,
        data: ClassData,
        current_pkg: str,
        pkg_cls_uuids: t.Iterable[str],
        pkg_deps: set[str],
        prop_name: str,
        custom_types: dict[str, str],
        built_ins: dict[str, str],
    ) -> str:
        if isinstance(prop_type, information.datatype.Enumeration):
            if prop_type.domain_type:
                base = RosExportHelper.type_name_for_datatype(
                    prop_type.domain_type, custom_types
                )
            else:
                logger.warning(
                    "Primitive type of %s should be added as domain_type, will use int32 instead",
                    prop_type.name,
                )
                base = DEFAULT_ENUM_TYPE
            for val in prop_type.owned_literals:
                data.literals.append(
                    LiteralData(
                        base,
                        f"{prop_name.upper()}_{RosExportHelper.make_snake_case(val.name).upper()}",
                        val.value.value,
                        RosExportHelper.make_doc_str(val.description),
                    )
                )
            return base
        if isinstance(prop_type, information.datatype.DataType):
            return RosExportHelper.type_name_for_datatype(
                prop_type, custom_types
            )
        if isinstance(prop_type, information.Class):
            prefix = ""
            is_builtin = False
            if prop_type.uuid not in pkg_cls_uuids:
                ref_pkg = class_to_pkg.get(prop_type.uuid)
                if ref_pkg and ref_pkg != current_pkg:
                    pkg_deps.add(ref_pkg)
                    is_builtin = ref_pkg in built_ins
                    if not is_builtin:
                        ref_pkg += self.pkg_postfix
                    prefix = f"{ref_pkg}/"
                elif ref_pkg is None:
                    logger.error(
                        "Class %s was referenced in %s, but not found",
                        prop_type.name,
                        ctx_cls.name,
                    )
            name = (
                prop_type.name
                if is_builtin
                else RosExportHelper.make_camel_case(prop_type.name)
            )
            return prefix + name
        logger.warning(
            "Unknown type for property %r of class %s",
            type(prop_type).__name__,
            ctx_cls.name,
        )
        return UNKNOWN_TYPE

    # ---------- Export ----------

    def export_ros_pkgs(
        self,
        out_dir: pathlib.Path,
        project_name: str,
        contact_email: str,
        maintainer: str,
    ) -> None:
        for pkg, msgs in self.data_packages.items():
            self._render_package(out_dir, pkg, msgs)
            self._write_pkg_information(
                out_dir,
                pkg,
                self.dependencies.get(pkg, []),
                contact_email,
                maintainer,
            )
        self._write_top_level_information(
            out_dir, project_name, self.dependencies, contact_email, maintainer
        )

    def _render_package(
        self, out_dir: pathlib.Path, name: str, msgs: list[ClassData]
    ) -> None:
        pkg_dir = out_dir / name / "msg"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        template = self.jinja_env.get_template("ros-msg.j2")
        for msg in msgs:
            (pkg_dir / f"{msg.name}.msg").write_text(
                template.render(msg=msg), "utf-8"
            )

    def _write_pkg_information(
        self,
        out_dir: pathlib.Path,
        name: str,
        dependencies: t.Iterable,
        contact_email: str,
        maintainer: str,
    ) -> None:
        pkg_dir = out_dir / name
        pkg_dir.mkdir(parents=True, exist_ok=True)
        if self.generate_cmake:
            cmake = self.jinja_env.get_template("cmake_pkg_level.j2").render(
                pkg_name=name + self.pkg_postfix, dependencies=dependencies
            )
            (pkg_dir / C_MAKE_LISTS_TXT).write_text(cmake, "utf-8")
        xml = self.jinja_env.get_template("package.xml.j2").render(
            pkg_name=name + self.pkg_postfix,
            dependencies=dependencies,
            contact_email=contact_email,
            maintainer=maintainer,
        )
        (pkg_dir / PACKAGE_XML).write_text(xml, "utf-8")

    def _write_top_level_information(
        self,
        out_dir: pathlib.Path,
        project_name: str,
        dependencies: t.Mapping[str, t.Iterable],
        contact_email: str,
        maintainer: str,
    ) -> None:
        dirs = topological_sort(dependencies)
        if self.generate_cmake:
            cmake = self.jinja_env.get_template("cmake_top_level.j2").render(
                project_name=project_name, directories=dirs
            )
            (out_dir / C_MAKE_LISTS_TXT).write_text(cmake, "utf-8")
        xml = self.jinja_env.get_template("top_level_package.xml.j2").render(
            project_name=project_name,
            contact_email=contact_email,
            maintainer=maintainer,
        )
        (out_dir / "package.xml").write_text(xml, "utf-8")
