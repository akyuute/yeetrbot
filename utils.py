import random
import inspect
from typing import Any, Union, Callable


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

def comb(
    obj: Union[list, dict],
    # func: Callable[Any],
    pred: Callable[Any, bool]) -> dict:
    '''Recurses through a dict or list, executing `func(dct[k])` whenever predicate
    `pred(obj[k])` returns True. Returns obj at the end.'''
    if isinstance(obj, list):
        return "Hmm."

    elif isinstance(obj, dict):
        for k in tuple(obj.keys()):
            # try:
            if pred(obj[k]):
                obj.pop(k)
                # func(obj[k])
            # except Exception:
                # comb(obj[k], pred)
                # pass
            else:
                comb(obj[k], pred)
                return obj

    # else:
        # print(obj)
        # raise TypeError("Bad type...")
    return obj


def remove_from_keys(
    obj: Union[list, dict],
    # func: Callable[Any],
    pred: Callable[Any, bool]) -> dict:
    '''Recurses through a dict or list, executing `func(dct[k])` whenever predicate
    `pred(obj[k])` returns True. Returns obj at the end.'''
    if isinstance(obj, list):
        return "Hmm."

    elif isinstance(obj, dict):
        for k in tuple(obj.keys()):
            # try:
            #if pred(obj[k]):
            if pred(k):
                obj.pop(k)
                # func(obj[k])
            # except Exception:
                # comb(obj[k], pred)
                # pass
            else:
                remove_from_keys(obj[k], pred)
                # return obj

    # else:
        # print(obj)
        # raise TypeError("Bad type...")
    return obj

def eprint(*objs):
    '''Prints "var =" f-strings so you don't have to, also retaining
    the original names of variables when called from anywhere.'''
    stack = inspect.stack()
    caller_frame = stack[-1].frame
    varnames = caller_frame.f_code.co_names[1:]
    for var, obj in zip(varnames, objs):
        print(f"{var} = {obj}")

