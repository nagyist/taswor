import multiprocessing
import os
import time
from collections import namedtuple

from taswor.util import get_logger
from taswor.util import Next


def worker_run(*args, **kwargs):
    Worker(*args, **kwargs).start()


class NodeProcessed:
    def __init__(self, from_node, from_args, from_kwargs, to_node, to_args, to_kwargs, duration, error):
        self.from_node = from_node
        self.from_args = from_args
        self.from_kwargs = from_kwargs
        self.to_node = to_node
        self.to_args = to_args
        self.to_kwargs = to_kwargs
        self.duration = duration
        self.error = error

    def to_dict(self):
        return self.__dict__

    def __str__(self):
        return repr(self.to_dict())


class Worker:
    def __init__(self, is_idle_event, queue, queue_lock, nodes, event_list, cache):
        self.is_idle_event = is_idle_event
        self.queue = queue
        self.queue_lock = queue_lock
        self.nodes = nodes
        self.events = event_list
        self.cache = cache

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

        if current_node.use_cache:
            # try searching in cache
            cache_key = "{}_{}_{}".format(current_node.name, args, kwargs)
            if cache_key in self.cache:
                # cache hit, save the cached result and return
                self.logger.info("Cached value {} ( {}, {} )".format(current_node.name, args, kwargs))
                self.process_result(self.cache[cache_key], current_node, args, kwargs, time.time())
                return

        start_time = time.time()
        try:
            result = current_node.resolve(*args, **kwargs)
        except Exception as e:
            self.logger.error("Node {} raised an exception: {}".format(current_node, e))
            self.logger.error("Was called with arguments {}, {}".format(args, kwargs))
            self.register_event((current_node.name, args, kwargs), None, time.time() - start_time, str(e))
            return

        self.logger.info("Node {}({}, {}) resolved to {}".format(current_node.name, args, kwargs, result))
        if current_node.use_cache:
            self.logger.info("Cache the result value")
            self.cache["{}_{}_{}".format(current_node.name, args, kwargs)] = result


        self.process_result(result, current_node, args, kwargs, start_time)

    def process_result(self, result, current_node, args, kwargs, start_time):
        if result is None:
            self.logger.debug("Node leaf encountered")
            self.register_event((current_node.name, args, kwargs), None, time.time() - start_time, None)
        elif isinstance(result, Next):
            # handle result
            node = self.get_node_from_next(result)
            self.queue.put((node, result.args, result.kwargs))
            self.register_event((current_node.name, args, kwargs), (node.name, result.args, result.kwargs),
                                time.time() - start_time, None)
        elif isinstance(result, list):
            for next_node in result:
                # handle next_node
                node = self.get_node_from_next(next_node)
                self.queue.put((node, next_node.args, next_node.kwargs))

                self.register_event((current_node.name, args, kwargs), (node.name, next_node.args, next_node.kwargs),
                                    time.time() - start_time, None)

    def register_event(self, current_node, next_node, duration, error=None):
        """

        :param current_node: a tuple (str, list/tuple, dict) representing (current_node_name, args, kwargs)
        :param next_node: a tuple (str, list/tuple, dict) representing (next_node_name, args, kwargs)
        :param duration: a float representing how many seconds the processing lasted
        :param error: None or a str representing an error message
        :return:
        """
        if not next_node:
            to_name = None
            to_args = None
            to_kwargs = None
        else:
            to_name = next_node[0]
            to_args = next_node[1]
            to_kwargs = next_node[2]

        self.events.append(
            NodeProcessed(from_node=current_node[0], from_args=current_node[1], from_kwargs=current_node[2],
                          to_node=to_name, to_args=to_args, to_kwargs=to_kwargs,
                          duration=duration, error=error))

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
