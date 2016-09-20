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
        args = [str(arg) for arg in args]
        kwargs = {k: str(v) for k, v in kwargs.items()}
        arguments = ", ".join(args + ["{}={}".format(k, v) for k, v in kwargs.items()])
        return node_name + " (" + arguments + ")"

    def check_if_edge(node1, node2, events):
        node1_name = node1["name"]
        node2_name = node2["name"]

        for event in events:
            if event.from_node == node1_name:
                for item in event.result:
                    if item.node_name == node2_name:
                        # possible match
                        return node1["args"] == event.args and node1["kwargs"] == event.kwargs \
                               and item.args == node2["args"] and item.kwargs == node2["kwargs"]

    nodes = []
    edges = {}

    # initial identification of nodes
    for event in event_list:
        nodes.append({"name": event.from_node, "args": event.args, "kwargs": event.kwargs,
                      "label": get_label(event.from_node, event.args, event.kwargs), "shape": "box", "color": "green"})

    nodes_unique = []
    for item in nodes:
        if len([n for n in nodes_unique if n["label"] == item["label"]]) == 0:
            nodes_unique.append(item)
    nodes = nodes_unique

    # create edges
    for node1, node2 in itertools.product(nodes, repeat=2):
        print(node1["label"], node2["label"])
        if check_if_edge(node1, node2, event_list):
            if node1["name"] in edges:
                edges[node1["name"]][node2["name"]] = {"directed": True}
            else:
                edges[node1["name"]] = {node2["name"]: {"directed": True}}

    return nodes, edges
