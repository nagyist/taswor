Introduction
============

Description
-----------

**Taswor** comes from **Task Workflow** and is a tool for building a workflow of tasks with support for visualising
the process flow. Basically, there are a few important concepts:

- **node bodies** - a function that represent what a node should do.
- **nodes** - a node body with associated arguments for the node body. Each node should return None if it is a leaf,
a node or a set of nodes otherwise.
- **workflow** - a set of node bodies that reference each other.


Architecture
------------

There are the following components:

- ``Workflow`` - the main controller of the application that manages other processes and the results.
- ``Worker`` - the processes that handle the events/nodes in a distributed manner.
- ``SharedMemoryManager`` - a process that acts like a shared memory between processes and handles the results, cache, etc.

