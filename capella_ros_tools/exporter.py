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
    """The exporter class."""

    packages: dict[str, str]  # mapping from ROS pkg name to capella pkg uuid
    build_ins: dict[str, str]  # maps build in ROS pkgs to capella pkg uuids
    package_uuids: list[str]  # list of all pkg uuids
    custom_pkg: dict[
        str, list[information.Class]
    ]  # maps ROS pkg names to capella classes
    custom_types: dict[str, str]  # maps custom capella types to ros types

    def __init__(
        self,
        packages: dict[str, str],
        build_ins: dict[str, str],
        custom_pkg: dict[str, list[str]],
        custom_types: dict[str, str],
        model: capellambse.MelodyModel,
        generate_cmake: bool,  # noqa: FBT001
        pkg_postfix: str | None = None,
    ) -> None:
        self.generate_cmake = generate_cmake
        self.model = model
        self.packages = packages
        self.build_ins = build_ins
        self.package_uuids = list(packages.values()) + list(build_ins.values())
        self.custom_types = custom_types
        self.custom_pkg = {
            pkg: [self.model.by_uuid(uuid) for uuid in uuids]
            for pkg, uuids in custom_pkg.items()
        }
        self.jinja_env = jinja2.Environment(
            loader=jinja2.PackageLoader(
                __name__.rsplit(".", 1)[0], PACKAGE_PATH
            )
        )
        self.pkg_postfix = pkg_postfix or ""

    def _get_package_classes(
        self,
        package: information.DataPkg,
        classes: list[information.Class] | None = None,
    ) -> list[information.Class]:
        if classes is None:
            classes = list(package.classes)
        else:
            classes += package.classes

        for sub_pkg in package.packages:
            if sub_pkg.uuid not in self.package_uuids:
                self._get_package_classes(sub_pkg, classes)

        return classes

    def _collect_pure_packages(
        self,
    ) -> dict[str, list[information.Class]]:
        package_class_mapping: dict[str, list[information.Class]] = {}
        for package_name, uuid in self.packages.items():
            package_class_mapping[package_name] = self._get_package_classes(
                self.model.by_uuid(uuid)
            )

        return package_class_mapping

    def _get_cls_dependencies(
        self,
        cls: information.Class,
        class_package_mapping: dict[str, str],
        dependency_classes: list[information.Class],
    ) -> None:
        for prop in cls.properties:
            _type = prop.type
            if isinstance(_type, information.Class):
                if (
                    _type.uuid in class_package_mapping
                    or _type in dependency_classes
                ):
                    continue

                dependency_classes.append(_type)
                self._get_cls_dependencies(
                    _type, class_package_mapping, dependency_classes
                )

    def _get_missing_dependencies(
        self,
        package_class_mapping: t.Mapping[str, t.Iterable[information.Class]],
        class_package_mapping: dict[str, str],
    ) -> dict[str, list[information.Class]]:
        dependency_classes: dict[str, list[information.Class]] = {}
        for pkg, classes in package_class_mapping.items():
            cls_dependencies: list[information.Class] = []
            dependency_classes[pkg] = cls_dependencies
            for cls in classes:
                self._get_cls_dependencies(
                    cls, class_package_mapping, cls_dependencies
                )
        return dependency_classes

    def _make_type_name(self, _type: information.datatype.DataType) -> str:
        type_name = _type.name
        if ros_type := self.custom_types.get(type_name):
            return ros_type

        if type_name in ROS_TYPES:
            return type_name

        if match := UINT_REGEX.match(type_name):
            length = RosExportHelper.int_bytes(int(match.group(1)))
            return f"uint{length}"

        if match := INT_REGEX.match(type_name):
            length = RosExportHelper.int_bytes(int(match.group(1)))
            return f"int{length}"

        if match := FLOAT_REGEX.match(type_name):
            length = RosExportHelper.float_bytes(int(match.group(1)))
            return f"float{length}"

        logger.error("Type %s is unknown.", type_name)
        return type_name

    def _create_class_data(
        self,
        cls: information.Class,
        current_pkg: str,
        class_package_mapping: dict[str, str],
        pkg_cls_uuids: t.Iterable[str],
        pkg_dependencies: set[str],
    ) -> ClassData:
        cls_data = ClassData(
            RosExportHelper.make_camel_case(cls.name),
            RosExportHelper.make_doc_str(cls.description),
        )
        for prop in cls.properties:
            _type = prop.type
            prop_name = RosExportHelper.make_snake_case(prop.name)
            type_name = self._handle_property_type(
                _type,
                class_package_mapping,
                cls,
                cls_data,
                current_pkg,
                pkg_cls_uuids,
                pkg_dependencies,
                prop_name,
            )

            try:
                card = (prop.min_card.value, prop.max_card.value)
            except AttributeError:
                card = ("1", "1")

            if card != ("1", "1"):
                if card[1] == "*":
                    type_name += "[]"
                elif card[0] == card[1]:
                    type_name += f"[{card[0]}]"
                else:
                    type_name += f"[<={card[1]}]"

            cls_data.literals.append(
                LiteralData(
                    type_name,
                    prop_name,
                    docstr=RosExportHelper.make_doc_str(prop.description),
                )
            )

        return cls_data

    def _handle_property_type(
        self,
        _type: capellambse.model.ModelElement,
        class_package_mapping: dict[str, str],
        cls: information.Class,
        cls_data: ClassData,
        current_pkg: str,
        pkg_cls_uuids: t.Iterable[str],
        pkg_dependencies: set[str],
        prop_name: str,
    ) -> str:
        if isinstance(_type, information.datatype.DataType):
            if isinstance(_type, information.datatype.Enumeration):
                if _type.domain_type:
                    type_name = self._make_type_name(_type.domain_type)
                else:
                    logger.warning(
                        "Primitive type of %s should be added as "
                        "domain_type, will use int32 instead",
                        _type.name,
                    )
                    type_name = DEFAULT_ENUM_TYPE
                for val in _type.owned_literals:
                    cls_data.literals.append(
                        LiteralData(
                            type_name,
                            f"{prop_name.upper()}_{RosExportHelper.make_snake_case(val.name).upper()}",
                            val.value.value,
                            RosExportHelper.make_doc_str(val.description),
                        )
                    )
            else:
                type_name = self._make_type_name(_type)
        elif isinstance(_type, information.Class):
            pkg = ""
            build_in = False
            if _type.uuid not in pkg_cls_uuids:
                if cls_pkg := class_package_mapping.get(_type.uuid):
                    if cls_pkg != current_pkg:
                        pkg_dependencies.add(cls_pkg)
                        build_in = cls_pkg in self.build_ins
                        if not build_in:
                            cls_pkg += self.pkg_postfix
                        pkg = f"{cls_pkg}/"
                else:
                    logger.error(
                        "Class %s was referenced in %s, but not found",
                        _type.name,
                        cls.name,
                    )

            type_name = pkg + (
                _type.name
                if build_in
                else RosExportHelper.make_camel_case(_type.name)
            )
        else:
            logger.warning(
                "Unknown type for property %r of class %s",
                type(_type).__name__,
                cls.name,
            )
            type_name = UNKNOWN_TYPE
        return type_name

    def _collect_build_in_classes(self) -> dict[str, str]:
        cls_to_pkg_mapping: dict[str, str] = {}
        for pkg_name, uuid in self.build_ins.items():
            for cls in self._get_package_classes(self.model.by_uuid(uuid)):
                cls_to_pkg_mapping[cls.uuid] = pkg_name

        return cls_to_pkg_mapping

    def prepare_export_data(
        self,
    ) -> tuple[dict[str, list[ClassData]], dict[str, set[str]]]:
        """Collect export data for all defined packages."""
        class_package_mapping = self._collect_build_in_classes()
        package_class_mapping = self._collect_pure_packages()
        # Built-in classes overwrite the mapping of classes from the config
        # E.g. PointCloud2 is defined as part of a custom package. If it is
        # also part of a built-in package, it won't be exported but referenced
        package_class_mapping |= {
            package: [
                cls for cls in classes if cls.uuid not in class_package_mapping
            ]
            for package, classes in self.custom_pkg.items()
        }
        class_package_mapping |= {
            cls.uuid: pkg_name
            for pkg_name, classes in package_class_mapping.items()
            for cls in classes
        }
        dependency_classes = self._get_missing_dependencies(
            package_class_mapping, class_package_mapping
        )
        seen_classes = set()
        duplicate_classes_uuids = set()
        multi_dependency_classes = []
        for clss in dependency_classes.values():
            for cls in clss:
                if cls.uuid not in seen_classes:
                    seen_classes.add(cls.uuid)
                elif cls.uuid not in duplicate_classes_uuids:
                    duplicate_classes_uuids.add(cls.uuid)
                    multi_dependency_classes.append(cls)

        result: dict[str, list[ClassData]] = {}
        pkg_dependencies: dict[str, set[str]] = {}

        if multi_dependency_classes:
            dependency_classes = {
                pkg: [
                    cls
                    for cls in clss
                    if cls.uuid not in duplicate_classes_uuids
                ]
                for pkg, clss in dependency_classes.items()
            }
            pkg = GENERIC_PKG_NAME
            pkg_dependencies[pkg] = set()
            result[pkg] = []
            for cls in multi_dependency_classes:
                class_package_mapping[cls.uuid] = pkg
                result[pkg].append(
                    self._create_class_data(
                        cls,
                        pkg,
                        class_package_mapping,
                        duplicate_classes_uuids,
                        pkg_dependencies[pkg],
                    )
                )

        for pkg, classes in package_class_mapping.items():
            pkg_dependencies[pkg] = set()
            pkg_cls_uuids = [
                cls.uuid
                for cls in itertools.chain(
                    classes, dependency_classes.get(pkg, [])
                )
            ]
            cls_uuids = set()
            result[pkg] = []
            for cls in classes:
                if cls.uuid not in cls_uuids:
                    cls_uuids.add(cls.uuid)
                    result[pkg].append(
                        self._create_class_data(
                            cls,
                            pkg,
                            class_package_mapping,
                            pkg_cls_uuids,
                            pkg_dependencies[pkg],
                        )
                    )

            for cls in dependency_classes.get(pkg, []):
                if cls.uuid not in cls_uuids:
                    cls_uuids.add(cls.uuid)
                    result[pkg].append(
                        self._create_class_data(
                            cls,
                            pkg,
                            class_package_mapping,
                            pkg_cls_uuids,
                            pkg_dependencies[pkg],
                        )
                    )

        return result, pkg_dependencies

    def export_ros_pkgs(
        self,
        out_dir: pathlib.Path,
        project_name: str,
        data_packages: dict[str, list[ClassData]],
        dependencies: dict[str, set[str]],
        contact_email: str,
        maintainer: str,
    ) -> None:
        """Export the given packages including CMake and package.xml files."""
        for pkg, msgs in data_packages.items():
            self._render_package(out_dir, pkg, msgs)
            self._write_pkg_information(
                out_dir,
                pkg,
                dependencies.get(pkg, []),
                contact_email,
                maintainer,
            )

        self._write_top_level_information(
            out_dir, project_name, dependencies, contact_email, maintainer
        )

    def _render_package(
        self, out_dir: pathlib.Path, name: str, msgs: list[ClassData]
    ) -> None:
        """Render the given messages for the given package."""
        pkg_dir = out_dir / name / "msg"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        template = self.jinja_env.get_template("ros-msg.j2")
        for msg in msgs:
            ros_msg = template.render(msg=msg)
            ros_path = pkg_dir / f"{msg.name}.msg"
            ros_path.write_text(ros_msg, "utf-8")

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
            cmake_template = self.jinja_env.get_template("cmake_pkg_level.j2")
            cmake_path = pkg_dir / C_MAKE_LISTS_TXT
            cmake_path.write_text(
                cmake_template.render(
                    pkg_name=name + self.pkg_postfix, dependencies=dependencies
                ),
                "utf-8",
            )
        xml_template = self.jinja_env.get_template("package.xml.j2")
        xml_path = pkg_dir / PACKAGE_XML
        xml_path.write_text(
            xml_template.render(
                pkg_name=name + self.pkg_postfix,
                dependencies=dependencies,
                contact_email=contact_email,
                maintainer=maintainer,
            ),
            "utf-8",
        )

    def _write_top_level_information(
        self,
        out_dir: pathlib.Path,
        project_name: str,
        dependencies: t.Mapping[str, t.Iterable],
        contact_email: str,
        maintainer: str,
    ) -> None:
        directories = topological_sort(dependencies)
        if self.generate_cmake:
            cmake_template = self.jinja_env.get_template("cmake_top_level.j2")
            cmake_path = out_dir / C_MAKE_LISTS_TXT
            cmake_path.write_text(
                cmake_template.render(
                    project_name=project_name, directories=directories
                ),
                "utf-8",
            )
        xml_template = self.jinja_env.get_template("top_level_package.xml.j2")
        xml_path = out_dir / "package.xml"
        xml_path.write_text(
            xml_template.render(
                project_name=project_name,
                contact_email=contact_email,
                maintainer=maintainer,
            ),
            "utf-8",
        )


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
