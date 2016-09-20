from collections import namedtuple

from taswor.util import get_logger


def event_manager_run(*args, **kwargs):
    EventManager(*args, **kwargs).start()


NodeProcessed = namedtuple("NodeProcessed", ["from_node", "to_node", "args", "kwargs", "result", "duration", "error"])


class EventManager:
    def __init__(self, event_queue):
        self.logger = get_logger("EventManager")
        self.event_queue = event_queue

        self.logger.info("Initialization complete")
        self.data = []

    def start(self):
        self.logger.info("Running")

        while True:
            event = self.event_queue.get()

            self.logger.info("Received event: {}".format(event))
            self.data.append(event)
