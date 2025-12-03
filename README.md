<!--
 ~ Copyright DB InfraGO AG and contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Capella ROS Tools

![image](https://github.com/dbinfrago/capella-ros-tools/actions/workflows/build-test-publish.yml/badge.svg)

Tools for importing ROS .msg files into Capella `DataPackage`, `DataType` and
`Class` objects, or exporting those objects to .msg files.

![Showcase](https://i.imgur.com/hs4EUnL.gif)

# Documentation

Read the [full documentation on Github pages](https://dbinfrago.github.io/capella-ros-tools).

# Examples

## Import of ROS Messages
Import local ROS .msg files to Capella model layer's root data package:

```sh
capella-ros-tools import \
-i tests/data/data_model/example_msgs \
-m tests/data/empty_project_60 \
-l la \
--no-deps
```

Import remote ROS .msg files to Capella model layer's root data package:

```sh
capella-ros-tools import \
-i git+https://github.com/DSD-DBS/dsd-ros-msg-definitions-oss \
-m tests/data/empty_project_60 \
-l la
```

## Export of Capella Classes as ROS2 Messages
Please mind: If classes don't follow the ROS2 naming conventions, their names as well as property, enumeration value and
package names will be converted accordingly.
### Export by layer
Export local Capella model layer's root data package as ROS .msg files. All msg files will be exported in a single
package:

```sh
capella-ros-tools export \
-m tests/data/melody_model_60 \
-l la \
-o tests/data/melody_msgs
```
Export remote Capella model layer's root data package as ROS .msg files. All msg files will be exported in a single
package:

```sh
capella-ros-tools export \
-m git+https://github.com/DSD-DBS/coffee-machine \
-l sa \
-o tests/data/coffee_msgs
```
### Custom Export
Use the custom exporter using a config file:
````yaml
packages:
    asdf: <capella_pkg_uuid>
built_ins:
    ros_pkg: <capella_build_in_pkg_uuid>
custom_pkg:
    "abc":
      - <capella_cls1_uuid>
    "xyz":
      - <capella_cls2_uuid>
custom_types:
    Bitset16: int16
    Bitset32: int32
````
This will generate three ROS packages. Package `asdf` will contain all classes listed in `capella_pkg` and sub-packages.
Package `abc` will contain `capella_cls1` and `xyz` will contain `capella_cls2`. If those classes use other classes as
types in their properties, these classes will be pulled in. In the `built_ins` section data packages can be defined,
which can be considered as built-in. So in this example, classes which are located in `capella_build_in_pkg` will not
be pulled into the packages and will be considered as available. These classes will be referenced using `ros_pkg` as ROS
package name. In `custom_types` a mapping of Capella types to ROS types can be provided for custom capella types.
```sh
capella-ros-tools export \
-m tests/data/melody_model_60 \
-c config.yaml \
-o tests/data/melody_msgs
```
The config file may also be provided as a jinja2 template, which will be rendered to the yaml described above during the
run. The jinja2 template will be rendered with the model provided in variable `model`. This way complex configurations
stay maintainable:
````yaml
packages: {}
built_ins:
    {% for pkg in model.search("DataPkg").by_name("ROS-Msgs").packages %}
    {{pkg.name}}: {{pkg.uuid}}
    {% endfor %}
custom_pkg:
    "abc":
      - <capella_cls1_uuid>
    "xyz":
      - <capella_cls2_uuid>
custom_types:
    Bitset16: int16
    Bitset32: int32
````

# Installation

You can install the latest released version directly from PyPI.

```sh
pip install capella-ros-tools
```

# Contributing

We'd love to see your bug reports and improvement suggestions! Please take a
look at our [guidelines for contributors](CONTRIBUTING.md) for details. It also
contains a short guide on how to set up a local development environment.

# Licenses

This project is compliant with the
[REUSE Specification Version 3.0](https://git.fsfe.org/reuse/docs/src/commit/d173a27231a36e1a2a3af07421f5e557ae0fec46/spec.md).

Copyright DB InfraGO AG, licensed under Apache 2.0 (see full text in
[LICENSES/Apache-2.0.txt](LICENSES/Apache-2.0.txt))

Dot-files are licensed under CC0-1.0 (see full text in
[LICENSES/CC0-1.0.txt](LICENSES/CC0-1.0.txt))
