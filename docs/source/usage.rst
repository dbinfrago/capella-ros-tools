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

   python -m capella_ros_tools import -i <INPUT> -m <MODEL> -l <LAYER> -p <PORT> --no-deps

*  **-i/--input**, import ROS2 messages from <INPUT>
*  **-m/--model**, export to Capella model <CAPELLA_MODEL_PATH>
*  **-l/--layer**, use Capella model layer <CAPELLA_MODEL_LAYER>
*  **-p/--port**, start Capella model explorer at <PORT> (optional)
*  **--no-deps**, do not import ROS2 dependencies (e.g. std_msgs) (flag)

.. note::
   The `--port` option can be used to start the Capella model explorer on a specific port. The Capella model viewer can then be downloaded to be viewed at a later time using `wget` eg. `wget http://localhost:<PORT> -E -r`.


Export Capella Model (experimental):
------------------------------------
.. code-block:: bash

   python -m capella_ros_tools export -m <MODEL> -l <LAYER> -o <OUTPUT>

* **-m/--model**, import Capella model from <MODEL>
* **-l/--layer**, use Capella model layer <LAYER>
* **-o/--output**, export ROS2 messages to <OUTPUT>
