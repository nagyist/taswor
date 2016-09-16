class Node:
    def __init__(self, func, name, start=False, init_generator=None):
        self.func = func
        self.name = name
        self.start = start
        self.init_generator = init_generator

    def resolve(self, *args, **kwargs):
        pass
