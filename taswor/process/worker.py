import multiprocessing
import os
import time

from taswor.util import get_logger
from taswor.util import Next
from taswor.process.event_manager import NodeProcessed


def worker_run(*args, **kwargs):
    Worker(*args, **kwargs).start()


class Worker:
    def __init__(self, is_idle_event, queue, queue_lock, event_message_queue, nodes):
        self.is_idle_event = is_idle_event
        self.queue = queue
        self.queue_lock = queue_lock
        self.event_mesage_queue = event_message_queue
        self.nodes = nodes

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

    def process_node(self, node, args, kwargs):
        result = None
        start_time = time.time()
        try:
            result = node.resolve(*args, **kwargs)
        except Exception as e:
            self.logger.error("Node {} raised an exception: {}".format(node, e))
            self.logger.error("Was called with arguments {}, {}".format(args, kwargs))
            self.event_mesage_queue.put(NodeProcessed(from_node=node.name, to_node=None, args=args, kwargs=kwargs,
                                                      result=None, duration=(time.time() - start_time), error=str(e)))

        self.logger.info("Node {}({}, {}) resolved to {}".format(node.name, args, kwargs, result))
        next_nodes = []
        if result is None:
            self.logger.debug("Node leaf encountered")
        elif isinstance(result, Next):
            # handle result
            node = self.get_node_from_next(result)
            next_nodes.append(node)
            self.queue.put((node, result.args, result.kwargs))
        elif isinstance(result, list):
            for next_node in result:
                # handle next_node
                node = self.get_node_from_next(next_node)
                next_nodes.append(node)
                self.queue.put((node, next_node.args, next_node.kwargs))
        self.event_mesage_queue.put(NodeProcessed(from_node=node.name, to_node=next_nodes, args=args, kwargs=kwargs,
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
