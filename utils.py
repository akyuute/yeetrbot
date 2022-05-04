def split_nth(it, n: int):
    if not hasattr(it, '__iter__'):
        raise TypeError(f"Can only split an iterable, not {type(it)}.")
    return (it[i:i+n] for i in range(0, len(it), n))

def join_with_or(it, sep: str = ", ", final: str = " or "):
    if not hasattr(it, '__iter__'):
        raise TypeError(f"Can only join an iterable, not {type(it)}.")
    return sep.join(it[:-1]) + final + it[-1]

