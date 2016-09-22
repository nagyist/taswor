Basic usage
===========

Next I will show how you can use this module and what you can accomplish with it.

Minimal example
---------------

Firstly, a minimal example is the following::


    from taswor import Workflow, node, Next

    start_args = [
        ((), {"number": 100}),
        ((), {"number": 101}),
        ((), {"number": 102}),
    ]


    @node(start=True, init_args=start_args)
    def initialisation(number):
        print(number)
        return [
            Next("add_one", number),
            Next("multiply_by_two", number)
        ]


    @node()
    def add_one(number):
        return Next("store_result", number + 1)


    @node()
    def multiply_by_two(number):
        number = number // 0

    @node()
    def store_result(*args, **kwargs):
        print(args, kwargs)


    if __name__ == '__main__':
        workflow = Workflow(
            initialisation.node, add_one.node, multiply_by_two.node, store_result.node
        )
        workflow.start()
        workflow.wait_for_completion()
        workflow.dump_result_as_html("test")
        workflow.close()


After we run the script, we will obtain a ``test`` directory in the current working directory with a ``index.html`` file.
The ``index.html`` file will contain a visualisation of the workflow:

.. image:: simple_image.png


The green nodes represent the starting nodes, the blue nodes represent the intermediary nodes that were processed
with success, the yellow nodes represent nodes that did not return anything (leaf nodes) and red nodes represent
nodes that raised an exception. When clicking a certain node, in the right panel will be displayed information about
the node processing.

Real-life example
-----------------

Let's assume we have a batch of images and we want to move them to certain directories, depending on its extension.
