class Node:
    def __init__(self, func, name, start=False, init_generator=None, use_cache=True):
        self.func = func
        self.name = name
        self.start = start
        self.init_generator = init_generator
        self.use_cache = use_cache

    def resolve(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return "<Node {} func={}>".format(self.name, self.func)
