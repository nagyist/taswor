import multiprocessing
import os
import time
from collections import namedtuple

from taswor.util import get_logger
from taswor.util import Next


def worker_run(*args, **kwargs):
    Worker(*args, **kwargs).start()


class NodeProcessed:
    def __init__(self, from_node, args, kwargs, result, duration, error):
        self.from_node = from_node
        self.args = args
        self.kwargs = kwargs
        self.result = result
        self.duration = duration
        self.error = error

    def to_dict(self):
        to_return = {
            "from": self.from_node,
            "to": [],
            "args": self.args,
            "kwargs": self.kwargs,
            "duration": self.duration,
            "error": self.error
        }
        if self.result is None:
            to_return["to"] = None
            return to_return
        elif not isinstance(self.result, list):
            self.result = [self.result]

        for item in self.result:
            to_return["to"].append({"name": item.node_name, "args": item.args, "kwargs": item.kwargs})

        return to_return

    def __str__(self):
        return repr(self.to_dict())


class Worker:
    def __init__(self, is_idle_event, queue, queue_lock, nodes, event_list):
        self.is_idle_event = is_idle_event
        self.queue = queue
        self.queue_lock = queue_lock
        self.nodes = nodes
        self.events = event_list

        self.worker_process = multiprocessing.current_process()
        self.logger = get_logger("Worker ".format(self.worker_process.name))

    def start(self):

        self.logger.debug("Worker {} started and waiting".format(os.getpid()))
        while True:
            self.is_idle_event.set()

            self.queue_lock.acquire()
            node, args, kwargs = self.queue.get()  # blocking

            self.is_idle_event.clear()
            self.queue_lock.release()

            self.logger.info("Received {}".format(node))
            self.process_node(node, args, kwargs)

    def process_node(self, current_node, args, kwargs):
        result = None
        start_time = time.time()
        try:
            result = current_node.resolve(*args, **kwargs)
        except Exception as e:
            self.logger.error("Node {} raised an exception: {}".format(current_node, e))
            self.logger.error("Was called with arguments {}, {}".format(args, kwargs))
            self.events.append(NodeProcessed(from_node=current_node.name, args=args, kwargs=kwargs,
                                             result=[], duration=(time.time() - start_time), error=str(e)))

        self.logger.info("Node {}({}, {}) resolved to {}".format(current_node.name, args, kwargs, result))
        if result is None:
            result = []
            self.logger.debug("Node leaf encountered")
        elif isinstance(result, Next):
            # handle result
            node = self.get_node_from_next(result)
            self.queue.put((node, result.args, result.kwargs))
            result = [result]
        elif isinstance(result, list):
            for next_node in result:
                # handle next_node
                node = self.get_node_from_next(next_node)
                self.queue.put((node, next_node.args, next_node.kwargs))
        self.events.append(NodeProcessed(from_node=current_node.name, args=args, kwargs=kwargs,
                                         result=result, duration=(time.time() - start_time), error=None))

    def get_node_from_next(self, next_instance):
        node_name = next_instance.node_name
        nodes = [node for node in self.nodes if node.name == node_name]
        if not nodes:
            self.logger.error("No node with name {} registered".format(node_name))
            raise RuntimeError("No node with name {} registered".format(node_name))
        if len(nodes) > 1:
            self.logger.error("Multiple nodes with name {} registered".format(node_name))
            raise RuntimeError("Multiple nodes with name {} registered".format(node_name))
        return nodes[0]
