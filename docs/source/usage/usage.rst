..
   Copyright DB InfraGO AG and contributors
   SPDX-License-Identifier: Apache-2.0

.. _howtos:

*****
Usage
*****

This section describes how to use the Capella ROS Tools CLI.

Importing ROS2 Messages:
------------------------
.. code-block:: bash

   $ python -m capella_ros_tools -i messages <ROS_MESSAGES_PATH> -o capella <CAPELLA_MODEL_PATH> -l <CAPELLA_MODEL_LAYER> --port=<PORT> --exists-action=<EXISTS_ACTION> --no-deps

Exporting Capella Models
------------------------
.. code-block:: bash

   $ python -m capella_ros_tools -i capella <CAPELLA_MODEL_PATH> -l <CAPELLA_MODEL_LAYER> -o messages <ROS_MESSAGES_PATH> --port <PORT>
