def split_nth(it, n: int):
    if not hasattr(it, '__iter__'):
        raise TypeError(f"Can only split an iterable, not {type(it)}.")
    return (it[i:i+n] for i in range(0, len(it), n))

def join_with_or(it, sep: str = ", ", final: str = " or "):
    if not hasattr(it, '__iter__'):
        raise TypeError(f"Can only join an iterable, not {type(it)}.")
    return sep.join(it[:-1]) + final + it[-1]

def str_to_bool(value: str):
    '''Returns `True` or `False` bools for truthy or falsy strings.'''
    truthy = "true t yes y on 1".split()
    falsy = "false f no n off 0".split()
    pattern = value.lower()
    if pattern not in truthy + falsy:
        raise ValueError(f"Invalid argument: {pattern!r}")
    match = pattern in truthy or not pattern in falsy
    return match

def get_rand_index(max_size: int, previous_val: int,
        repeat_prob: float|int, min_size: int = 0):
    '''Returns a random integer with a specified probability that it
    differs from a previous value.'''
    index = previous_val
    while min_size <= index == previous_val and repeat_prob < random.random():
        index = int(random.random() * max_size)
    return index

