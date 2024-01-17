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

   $ python -m capella_ros_tools import <ROS_MESSAGES_PATH> <CAPELLA_MODEL_PATH> <CAPELLA_MODEL_LAYER> --port=<PORT> --exists-action=<EXISTS_ACTION> --no-deps

*  **<ROS_MESSAGES_PATH>**, import ROS2 messages from <ROS_MESSAGES_PATH>
*  **<CAPELLA_MODEL_PATH>**, export to Capella model <CAPELLA_MODEL_PATH>
*  **<CAPELLA_MODEL_LAYER>**, use Capella model layer <CAPELLA_MODEL_LAYER>
*  **--port=<PORT>**, start Capella model server at <PORT> (optional)
*  **--exists-action=<EXISTS_ACTION>**, action to take if a Capella element already exists (optional)

   * **skip**, skip elements
   * **replace**, replace elements
   * **abort**, abort import
   * **ask**, ask the user (default)

*  **--no-deps**, do not import ROS2 dependencies (e.g. std_msgs)

Export Capella Model (experimental):
------------------------------------
.. code-block:: bash

   $ python -m capella_ros_tools export <CAPELLA_MODEL_PATH> <CAPELLA_MODEL_LAYER> <ROS_MESSAGES_PATH>

* **<CAPELLA_MODEL_PATH>**, import Capella model from <CAPELLA_MODEL_PATH>
* **<CAPELLA_MODEL_LAYER>**, use Capella model layer <CAPELLA_MODEL_LAYER>
* **<ROS_MESSAGES_PATH>**, export ROS2 messages to <ROS_MESSAGES_PATH>
