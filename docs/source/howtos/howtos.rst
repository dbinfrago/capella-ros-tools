..
   Copyright DB InfraGO AG and contributors
   SPDX-License-Identifier: Apache-2.0

.. _howtos:

*******
Examples
*******

This section contains a collection of examples that demonstrate how to use the library.

Using the CLI
=============

Import ROS2 Messages:
------------------------
.. code-block:: bash

   $ python -m capella_ros_tools -i messages docs/source/examples/data/example_msgs -o capella docs/source/examples/data/empty_project_52 -l la --port 5000 --exists-action=k --no-deps

Import ROS2 Messages from Git Repository:
------------------------
.. code-block:: bash

   $ python -m capella_ros_tools -i messages git+https://github.com/DSD-DBS/dsd-ros-msg-definitions-oss -o capella docs/source/examples/data/empty_project_52 -l la --port 5000 --exists-action=k

Export Capella Model
---------------------
.. code-block:: bash

   $ python -m capella_ros_tools -i capella docs/source/examples/data/melody_model_60 -l la -o messages docs/source/examples/data/example_msgs --port 5000

Export Capella Model from Git Repository:
------------------------
.. code-block:: bash

   $ python -m capella_ros_tools -i capella git+https://github.com/DSD-DBS/coffee-machine -l la -o messages docs/source/examples/data/coffee_msgs --port 5000


Using the Python API
====================

In this section you can view dedicated tutorial-notebooks that demonstrate how to use the library.

.. toctree::
   :maxdepth: 4
   :caption: How tos:
   :numbered:
   :glob:

   ../examples/*
