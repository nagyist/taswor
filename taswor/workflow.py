import os
import multiprocessing
from multiprocessing import Queue, Event

from taswor.util import Next
from taswor.node import Node


class Workflow:
    def __init__(self, *nodes, workers=os.cpu_count(), cache_url=None, storage_url=None):
        self.nodes = nodes
        self.queue = Queue()
        self.workers = [multiprocessing.Process(target=self.worker_loop, name="worker-{}".format(i)) for i in
                        range(workers)]
        for worker in self.workers:
            worker.start()

    def process(self):
        start_nodes = self._get_start_nodes()

        for node in start_nodes:
            if not node.init_generator:
                self.queue.put((node, (), {}))
            else:
                for args, kwargs in node.init_generator:
                    self.queue.put((node, args, kwargs))

        for worker in self.workers:
            worker.join()

    def _get_start_nodes(self):
        return [node for node in self.nodes if node.start]

    def worker_loop(self):
        print("Worker {} starterd and waiting".format(os.getpid()))
        while True:
            node, args, kwargs = self.queue.get()
            print("Got {}".format(node))
            result = node.resolve(*args, **kwargs)
            print("Node {}({}, {}) resolved to {}".format(node.name, args, kwargs, result))

            if result is None:
                print("Node leaf encountered")
                pass
            elif isinstance(result, Next):
                # handle result
                node = self.get_node_from_next(result)
                self.queue.put((node, result.args, result.kwargs))
            elif isinstance(result, list):
                for next_node in result:
                    # handle next_node
                    node = self.get_node_from_next(next_node)
                    self.queue.put((node, next_node.args, next_node.kwargs))

    def get_node_from_next(self, next_instance):
        node_name = next_instance.node_name
        nodes = [node for node in self.nodes if node.name == node_name]
        if not nodes:
            raise RuntimeError("No node with name {} registered".format(node_name))
        if len(nodes) > 1:
            raise RuntimeError("Multiple nodes with name {} registered".format(node_name))
        return nodes[0]


def test():
    return Next("test2", 1, 2, 3, 10, item="a")


def test2(*args, **kwargs):
    print("test2 called with {} and {}".format(args, kwargs))


if __name__ == '__main__':
    workflow = Workflow(
        Node(name="test", func=test, start=True),
        Node(name="test2", func=test2)
    )
    workflow.process()
