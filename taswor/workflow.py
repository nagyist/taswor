import multiprocessing

from taswor.util import Next


class Workflow:
    def __init__(self, *nodes, workers=1):
        self.nodes = nodes
        self.worker_pool = multiprocessing.Pool(processes=workers)

    def process(self):
        pass
