..
   Copyright DB InfraGO AG and contributors
   SPDX-License-Identifier: Apache-2.0

.. _usage:

*****
Usage
*****

This section describes how to use the Capella ROS Tools CLI.

Import ROS2 Messages:
----------------------
.. code-block:: bash

   python -m capella_ros_tools import -i <INPUT> -m <MODEL> -l <LAYER> -o <OUTPUT> --no-deps

*  **-i/--input**, import ROS2 messages from path <INPUT>
*  **-m/--model**, write to Capella model at path <MODEL>
*  **-l/--layer**, use Capella model layer <LAYER>
*  **-o/--out**, write generated decl YAML to path <OUT> (optional)
*  **--no-deps**, flag to disable import of ROS2 dependencies (e.g. std_msgs)

Export Capella Model (experimental):
------------------------------------
.. code-block:: bash

   python -m capella_ros_tools export -m <MODEL> -l <LAYER> -o <OUTPUT>

* **-m/--model**, export Capella model from path <MODEL>
* **-l/--layer**, use Capella model layer <LAYER>
* **-o/--output**, write ROS2 messages to <OUTPUT>
