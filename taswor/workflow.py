import os
import sys
from multiprocessing import Queue, Event, Process, RLock, Manager
import logging
import time

pass

from taswor.util import Next, get_logger
from taswor.node import Node
from taswor.process.worker import worker_run
from taswor.process.event_manager import event_manager_run


class Workflow:
    def __init__(self, *nodes, workers=os.cpu_count(), cache_url=None, storage_url=None):
        self.nodes = nodes
        self.queue = Queue()
        self.queue_lock = RLock()
        self.is_idle = [Event() for _ in range(workers)]
        self.logger = get_logger("WorkflowMain")

        self.logger.info("Starting EventManager")
        self.event_message_queue = Queue()
        self.event_manager = Process(target=event_manager_run, args=(self.event_message_queue,))
        self.event_manager.start()

        if not cache_url:
            self.logger.warning("No cache backend supplied. Results will not be cached and may have a serious "
                                "performance impact")
        if not storage_url:
            self.logger.warning("No storage backend supplied. Storage usage inside the Node instances will be ignored")

        self.logger.info("Starting workers")
        self.workers = [
            Process(target=worker_run,
                    args=(self.is_idle[i], self.queue, self.queue_lock, self.event_message_queue, self.nodes),
                    name="worker-{}".format(i))
            for i in range(workers)]

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

        finished = False
        while not finished:
            if self._all_workers_are_idle():
                self.logger.info("Terminating")
                finished = True
                for worker in self.workers:
                    worker.terminate()
                    worker.join()

                self.event_manager.terminate()

    def _get_start_nodes(self):
        return [node for node in self.nodes if node.start]

    def _all_workers_are_idle(self):
        time.sleep(1)
        x = [event.is_set() for event in self.is_idle]
        return all(x)


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
