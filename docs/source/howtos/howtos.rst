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

   $ python -m capella_ros_tools import docs/source/examples/data/example_msgs docs/source/examples/data/empty_project_52 la --exists-action=keep --port=5000 --no-deps

Import ROS2 Messages from Git Repository:
-----------------------------------------
.. code-block:: bash

   $ python -m capella_ros_tools import git+https://github.com/DSD-DBS/dsd-ros-msg-definitions-oss docs/source/examples/data/empty_project_52 la --exists-action=keep --port=5000

Export Capella Model (experimental):
------------------------------------
.. code-block:: bash

   $ python -m capella_ros_tools export docs/source/examples/data/melody_model_60 la docs/source/examples/data/example_msgs

Export Capella Model from Git Repository (experimental):
--------------------------------------------------------
.. code-block:: bash

   $ python -m capella_ros_tools export git+https://github.com/DSD-DBS/coffee-machine la docs/source/examples/data/coffee_msgs


Using the Python API
====================

In this section you can view dedicated tutorial-notebooks that demonstrate how to use the library.

.. toctree::
   :maxdepth: 4
   :caption: How tos:
   :numbered:
   :glob:

   ../examples/*
