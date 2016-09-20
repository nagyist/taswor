import logging
import sys

class Next:
    def __init__(self, node_name, *args, **kwargs):
        self.node_name = node_name
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return "<NextNode -> {}( {}, {} )>".format(self.node_name, self.args, self.kwargs)


def get_logger(name=None):
    if not name:
        name = __name__
    logger = logging.Logger(name)
    format = "[%(asctime)s][%(process)s][%(levelname).1s] %(message)s"

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(format))
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

    logger.setLevel(logging.DEBUG)
    return logger
