class Next:
    def __init__(self, node_name, *args, **kwargs):
        self.node_name = node_name
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return "<NextNode -> {}( {}, {} )>".format(self.node_name, self.args, self.kwargs)
