import logging
import sys
import itertools


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


def preprocess_events(event_list):
    def get_label(node_name, args, kwargs):
        if not node_name:
            return "leaf_node (stop)"
        args = [str(arg) for arg in args] if args else []
        kwargs = {k: str(v) for k, v in kwargs.items()} if kwargs else {}
        arguments = ", ".join(args + ["{}={}".format(k, v) for k, v in kwargs.items()])
        return node_name + " (" + arguments + ")"

    nodes = {}
    edges = {}

    # get edges and nodes
    for event in event_list:
        current_node = event.from_node
        current_args = event.from_args
        current_kwargs = event.from_kwargs

        next_node = event.to_node
        next_args = event.to_args
        next_kwargs = event.to_kwargs

        duration = event.duration
        error = event.error

        current_label = get_label(current_node, current_args, current_kwargs)
        next_label = get_label(next_node, next_args, next_kwargs)

        if current_label in edges:
            edges[current_label][next_label] = {"directed": True, "duration": duration, "error": error,
                                                "color": "red" if error else "green"}
        else:
            edges[current_label] = {
                next_label: {
                    "directed": True, "duration": duration, "error": error,
                    "color": "red" if error else "green"
                }
            }

        if current_label not in nodes:
            nodes[current_label] = {"label": current_label, "shape": "box", "color": "blue"}
        if next_label == "leaf_node (stop)":
            nodes[next_label] = {"label": next_label, "shape": "box", "color": "red"}

    print(nodes, edges)

    return nodes, edges
