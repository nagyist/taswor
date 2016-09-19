import os
import sys
from multiprocessing import Queue, Event, Process, RLock, Manager
import logging
import time
import functools

from taswor.util import Next
from taswor.node import Node


class Workflow:
    def __init__(self, *nodes, workers=os.cpu_count(), cache_url=None, storage_url=None):
        self.nodes = nodes
        self.queue = Queue()
        self.queue_lock = RLock()
        self.is_idle = [Event() for _ in range(workers)]

        self.manager = Manager()
        # self.workflow_info = self.manager.dict()

        # cannot pickle loggers and worker instantiation will fail if self.logger is a logging.Logger instance
        self.logger = None

        self.workers = [
            Process(target=self.worker_loop, args=(self.is_idle[i], self.queue_lock), name="worker-{}".format(i))
            for i in range(workers)]
        for worker in self.workers:
            worker.start()

        self.logger = self.get_logger()

        if not cache_url:
            self.logger.warning("No cache backend supplied. Results will not be cached and may have a serious "
                                "performance impact")
        if not storage_url:
            self.logger.warning("No storage backend supplied. Storage usage inside the Node instances will be ignored")

    def get_logger(self):
        logger = logging.Logger(__name__)
        format = "[%(asctime)s][%(process)s][%(levelname).1s] %(message)s"

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(format))
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)

        logger.setLevel(logging.DEBUG)
        return logger

    def process(self):
        start_nodes = self._get_start_nodes()

        for node in start_nodes:
            if not node.init_generator:
                self.queue.put((node, (), {}))
            else:
                for args, kwargs in node.init_generator:
                    self.queue.put((node, args, kwargs))

        finished = False
        while not finished:
            if self._all_workers_are_idle():
                self.logger.info("Terminating")
                finished = True
                for worker in self.workers:
                    worker.terminate()
                    worker.join()

    def _get_start_nodes(self):
        return [node for node in self.nodes if node.start]

    def _all_workers_are_idle(self):
        time.sleep(1)
        x = [event.is_set() for event in self.is_idle]
        return all(x)

    def worker_loop(self, is_idle_event, queue_lock):
        self.logger = self.get_logger()
        self.logger.debug("Worker {} started and waiting".format(os.getpid()))
        while True:
            is_idle_event.set()

            queue_lock.acquire()
            node, args, kwargs = self.queue.get()  # blocking

            is_idle_event.clear()
            queue_lock.release()

            self.logger.info("Received {}".format(node))
            result = None
            try:
                result = node.resolve(*args, **kwargs)
            except Exception as e:
                self.logger.error("Node raised an exception: {}".format(e))

            self.logger.info("Node {}({}, {}) resolved to {}".format(node.name, args, kwargs, result))

            if result is None:
                self.logger.debug("Node leaf encountered")
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
            self.logger.error("No node with name {} registered".format(node_name))
            raise RuntimeError("No node with name {} registered".format(node_name))
        if len(nodes) > 1:
            self.logger.error("Multiple nodes with name {} registered".format(node_name))
            raise RuntimeError("Multiple nodes with name {} registered".format(node_name))
        return nodes[0]


def node(retries=1, start=False, init_args_generator=None):
    def decorator(func):
        node = Node(name=func.__name__, func=func, start=start, init_generator=init_args_generator, retries=retries)
        func.node = node
        return func

    return decorator


@node(start=True)
def test():
    time.sleep(1)
    return [
        Next("test2", 1, 2, 3, 10, item="a"),
        Next("test3"),
        Next("test2", string="hello world"),
    ]


@node()
def test2(*args, **kwargs):
    time.sleep(0.5)
    print("test2 called with {} and {}".format(args, kwargs))
    time.sleep(0.25)
    return Next("test3")


@node()
def test3():
    time.sleep(1)


if __name__ == '__main__':
    workflow = Workflow(
        test.node, test2.node, test3.node,
        workers=4
    )
    workflow.process()
