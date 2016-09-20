import os
import sys
import json
import shutil
from multiprocessing import Queue, Event, Process, RLock, Manager
import time

pass

from taswor.util import Next, get_logger
from taswor.node import Node
from taswor.process.worker import worker_run


class Workflow:
    def __init__(self, *nodes, workers=os.cpu_count(), cache_url=None, storage_url=None):
        self.nodes = nodes
        self.queue = Queue()
        self.queue_lock = RLock()
        self.is_idle = [Event() for _ in range(workers)]
        self.logger = get_logger("WorkflowMain")

        self.manager = Manager()
        self.events = self.manager.list()

        if not cache_url:
            self.logger.warning("No cache backend supplied. Results will not be cached and may have a serious "
                                "performance impact")
        if not storage_url:
            self.logger.warning("No storage backend supplied. Storage usage inside the Node instances will be ignored")

        self.logger.info("Starting workers")
        self.workers = [
            Process(target=worker_run,
                    args=(self.is_idle[i], self.queue, self.queue_lock, self.nodes, self.events),
                    name="worker-{}".format(i))
            for i in range(workers)]

        for worker in self.workers:
            worker.start()

    def start(self, wait=False):
        start_nodes = self._get_start_nodes()

        for node in start_nodes:
            if not node.init_generator:
                self.queue.put((node, (), {}))
            else:
                for args, kwargs in node.init_generator:
                    self.queue.put((node, args, kwargs))

        if wait:
            self.wait_for_completion()

    def close(self):
        self.logger.info("Closing all workers")
        for worker in self.workers:
            worker.terminate()
            worker.join()

        self.logger.info("All workers killed")

        self.logger.info("Terminating")

    def wait_for_completion(self):
        self.logger.debug("Waiting for completion")
        finished = False
        while not finished:
            if self._all_workers_are_idle():
                self.logger.info("Finished")
                finished = True

    def dump_result_as_json(self, filename):
        import json
        with open(filename, "w") as out:
            data = {"raport": [x.to_dict() for x in self.events]}
            json.dump(data, out, indent=4, sort_keys=True)

    def dump_result_as_html(self, directory):
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "html")
        shutil.copytree(template_dir, directory)

        def get_node(event):
            name = event.from_node
            label = name + " (" + repr(event.args) + "," + repr(event.kwargs) + ")"
            color = "green" if not event.error else "red"

            return label, {"shape": "box", "label": label, "color": color}

        data = {
            "nodes": {},
            "edges": {}
        }
        for event in self.events:
            node_name, attrs = get_node(event)
            data["nodes"][node_name] = attrs

        with open(os.path.join(directory, "data.json"), "w") as data_json:
            data_json.write("data=")
            data_json.write(json.dumps(data))
            data_json.write(";")

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

    workflow.start()
    workflow.wait_for_completion()
    workflow.dump_result_as_html("test")
    workflow.close()
