..
   Copyright DB InfraGO AG and contributors
   SPDX-License-Identifier: Apache-2.0

.. _howtos:

********
Examples
********

This section contains a collection of examples that demonstrate how to use the library.

Using the CLI
=============

Import ROS2 Messages:
---------------------
.. code-block:: bash

   $ python -m capella_ros_tools import tests/data/example_msgs tests/data/empty_model la --exists-action=skip --port=5000 --no-deps

Import ROS2 Messages from Git Repository:
-----------------------------------------
.. code-block:: bash

   $ python -m capella_ros_tools import git+https://github.com/DSD-DBS/dsd-ros-msg-definitions-oss tests/data/empty_model la --exists-action=skip --port=5000

Export Capella data package:
------------------------------------
.. code-block:: bash

   $ python -m capella_ros_tools export tests/data/melody_model_60 la tests/data/melody_msgs

Export Capella data package from Git Repository (experimental):
--------------------------------------------------------
.. code-block:: bash

   $ python -m capella_ros_tools export git+https://github.com/DSD-DBS/coffee-machine oa tests/data/coffee_msgs
