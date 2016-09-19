class Node:
    def __init__(self, func, name, start=False, init_generator=None, retries=1):
        self.func = func
        self.name = name
        self.start = start
        self.init_generator = init_generator
        self.retries = 1

    def resolve(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return "<Node {} func={}>".format(self.name, self.func)
