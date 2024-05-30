<!--
 ~ Copyright DB InfraGO AG and contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Capella ROS Tools

![image](https://github.com/DSD-DBS/capella-ros-tools/actions/workflows/build-test-publish.yml/badge.svg)
![image](https://github.com/DSD-DBS/capella-ros-tools/actions/workflows/lint.yml/badge.svg)

Tools for importing ROS .msg files into Capella `DataPackage`, `DataType` and
`Class` objects, or exporting those objects to .msg files.

![Showcase](https://i.imgur.com/hs4EUnL.gif)

# Documentation

Read the [full documentation on Github pages](https://dsd-dbs.github.io/capella-ros-tools).

# Examples

Import local ROS .msg files to Capella model layer's root data package:

```sh
python -m capella_ros_tools \
import \
-i tests/data/data_model/example_msgs \
-m tests/data/empty_project_60 \
-l la \
--no-deps
```

Import remote ROS .msg files to Capella model layer's root data package:

```sh
python -m capella_ros_tools \
import \
-i git+https://github.com/DSD-DBS/dsd-ros-msg-definitions-oss \
-m tests/data/empty_project_60 \
-l la
```

Export local Capella model layer's root data package as ROS .msg files:

```sh
python -m capella_ros_tools \
export \
-m tests/data/melody_model_60 \
-l la \
-o tests/data/melody_msgs
```

Export remote Capella model layer's root data package as ROS .msg files:

```sh
python -m capella_ros_tools \
export \
-m git+https://github.com/DSD-DBS/coffee-machine \
-l sa \
-o tests/data/coffee_msgs
```

# Installation

You can install the latest released version directly from PyPI.

```sh
pip install capella-ros-tools
```

To set up a development environment, clone the project and install it into a
virtual environment.

```sh
git clone https://github.com/DSD-DBS/capella-ros-tools
cd capella-ros-tools
python -m venv .venv

source .venv/bin/activate.sh  # for Linux / Mac
.venv\Scripts\activate  # for Windows

pip install -U pip pre-commit
pip install -e '.[docs,test]'
pre-commit install
```

# Contributing

We'd love to see your bug reports and improvement suggestions! Please take a
look at our [guidelines for contributors](CONTRIBUTING.md) for details.

# Licenses

This project is compliant with the
[REUSE Specification Version 3.0](https://git.fsfe.org/reuse/docs/src/commit/d173a27231a36e1a2a3af07421f5e557ae0fec46/spec.md).

Copyright DB InfraGO AG, licensed under Apache 2.0 (see full text in
[LICENSES/Apache-2.0.txt](LICENSES/Apache-2.0.txt))

Dot-files are licensed under CC0-1.0 (see full text in
[LICENSES/CC0-1.0.txt](LICENSES/CC0-1.0.txt))
