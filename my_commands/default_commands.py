import re
import random
import string

many_years = "Many years later, as he faced the firing squad, Colonel Aureliano Buendia was to remember that distant afternoon when his father took him to discover ice."

def _get_rand_index(max_size: int, previous_val: int, repeat_prob: float|int, min_size: int=0):
    """Returns a random integer with a specified probability that it differs from a previous value."""
    index = previous_val
    while min_size <= index == previous_val and repeat_prob < random.random():
        index = int(random.random() * max_size)
    return index

def uwu(msg: str = many_years):
    """Translates a string to UwU speak."""
    try:
        if type(msg) != str:
            raise TypeError("Not a valid string.")
        elif len(msg) == 0:
            raise ValueError("Please enter a message to be translated.")
        resp = msg
        # matches = ("l", "L", "r", "R", "I", " the ", " The ", " that ", " That ", "th", )
        matches = (r"[lr]", r"[LR]", "I", r"(?<=\W)the(?=\W)", r"(?<=\W)The(?=\W)",
            r"(?<=\W)that(?=\W)", r"(?<=\W)That(?=\W)", r"(?<=\W)th", "th", )
        repls = ("w", "W", "i", "teh", "Teh", "dat", "Dat", "f", ("t", "v", "d"), )

        for i, repl in enumerate(repls):
        # first, make unconditional replacements
            if isinstance(repl, list|tuple):
            # for replacements with multiple possible values,
            # we randomize which value gets chosen.
                rand_index = 0
                for _ in range(resp.count(matches[i])):
                    rand_index = _get_rand_index(len(repl), rand_index, 0.2)
                    resp = re.sub(matches[i], repl[rand_index], resp, 1)
                continue
            resp = re.sub(matches[i], repl, resp)
        resp = resp.split()
        # cond_repls = {r"[a-zA-Z]": (f"{word[0].lower()}-{word[0]}", 0.99), "u": ("uwu", 0.99), "U": ("UwU", 0.1), }
        # for match, repl in cond_repls.items():
        for i, word in enumerate(resp):
        # now, make conditional replacements
            if random.random() < 0.1:
                # resp[i] = re.sub(r"[a-zA-Z]", f"{word[0].lower()}-{word[0]}", word))
                resp[i] = f"{word[0].lower()}-{word}" # stuttering
                continue
            if random.random() < 0.2:
                resp[i] = word.replace("u", "uwu", 1)
                continue
            if random.random() < 0.5:
                resp[i] = word.replace("U", "UwU", 1)
                continue
                    # resp[i] = re.sub(r"[a-zA-Z]", f"{resp[i][0].lower()}-{resp[i][0]}", word, 1) #r"\g<0>-\g<0>", word, 1)
                    # resp[i] = re.sub(match, repl[0], word)
        resp = " ".join(resp) + " UwU"
        return resp, 0
    except (TypeError, ValueError) as exc:
        return exc.args[0], 1
    except Exception as exc:
        return exc.args[0], 1
        # logger.exception("Unexpected error: ")



def derp(msg: str):
    try:
        if type(msg) != str:
            raise TypeError("Not a valid string.")
        elif len(msg) == 0:
            raise ValueError("Please enter a message to be translated.")
        resp = list(msg)
        do_upper = False
        for i, char in enumerate(resp):
            if char == "I":
                resp[i] = "i" 
            elif char != "i":
                do_upper = not do_upper if random.random() < 0.8 else do_upper
                resp[i] = char.upper() if do_upper else char.lower()
        return "".join(resp), 0
    except (TypeError, ValueError) as exc:
        return exc.args[0], 1
    except Exception as exc:
        return exc.args[0], 1
        # logger.exception("Unexpected error: ")




def uhm(msg: str):
    """Returns a string that is very unsure of itself."""
    try:
        if type(msg) != str:
            raise TypeError("Not a valid string.")
        elif len(msg) == 0:
            raise ValueError("Please enter a message to be translated.")
        # using a dict of form str_len: prob, set up a variable for the
        # probability of string operations depending on string length:
        prob_per_len = {0: 2.5, 5: 2, 10: 1.25, 15: 1.25, 20: 1}
        # reference dict by length rounded down to nearest multiple of 5:
        global_prob = prob_per_len[min(20, len(msg) // 5 * 5)]
        # begin string operations:
        resp = list(msg)
        for i, char in enumerate(resp):
            if resp[i-1] == " " and re.match(r"\w", char) and random.random() < global_prob * 0.15:
                resp[i] = char + "-" + char # stuttering
            if char == " " and resp[i-1] != "." and random.random() < global_prob * 0.2:
                 # random "uhm"s and "uh[h]"s:
                resp[i] = f""", uh{'m' if random.random() < 0.6 else
                'h' * random.randint(0,1)}, """ if resp[i-1] != "," else " uhm, "
                 # random "..."s, if not one of the above:
            elif char == " " and resp[i-1] != "," and random.random() < 0.1: resp[i] = "..."
        return "".join(resp) + "...", 0
    except (TypeError, ValueError) as exc:
        return exc.args[0], 1
    except Exception as exc:
        return exc.args[0], 1
        # logger.exception("Unexpected error: ")




def ye(msg: str):
    try:
        if type(msg) != str:
            raise TypeError("Not a valid string.")
        elif len(msg) == 0:
            raise ValueError("Please enter a message to be translated.")
        pass
    except (TypeError, ValueError) as exc:
        return exc.args[0]
    except Exception as exc:
    # logger.exception("Unexpected error: ")
        return exc.args[0]


def imdad(msg: str, prefix: tuple = ("i'm ", "i am ", "im "), maxlen: int = 20):
    '''Does what dads do best:
    Returns "Hi <message body>, I'm Dad." for messages under maxlen.'''
    try:
        if type(msg) != str:
            raise TypeError(f"{msg}: Not a valid string.")
        elif len(msg) == 0:
            # raise ValueError("Please enter a message to be translated.")
            return
    except (TypeError, ValueError) as exc:
        # return exc.args[0]
        pass
    except Exception as exc:
    # logger.exception("Unexpected error: ")
        # return exc.args[0]
        pass
    if len(msg) > maxlen:
        return
    elif msg[:6].lower().startswith(prefix):
        for match in prefix:
            msg = re.sub(match, "", msg, flags=re.IGNORECASE)
        return f"Hi {msg.rstrip(string.punctuation)}, I'm Dad.", 0
    else:
        return


def woahthere(msg: str):
    '''Returns one of several shocked reactions when someone uses mashing.'''
    pass

def shuffle_words(msg: str):
    '''Returns a syntactically correct message with word order and punctuation randomized.'''
    chars = r'[!&,.:;?]+'
    match = re.compile(chars)
    punct = match.findall(msg)
    words = match.sub(' ', msg).split()
    punct += [''] * (len(words) - len(punct))
    ends = ['!', '?', '.']
    random.shuffle(words)
    random.shuffle(punct)
    resp = []
    for w in words:
        if w.lower() in ("the", "of", ):
            w = w.lower()
        if len(resp) == 0:
            if punct[-1] in ends + ['...']:
                resp.insert(0, w + punct.pop())
            else:
                resp.insert(0, w + '.')
            continue
        add = punct.pop()
        resp.insert(0, w + add)
        if add in ends:
            resp[1] = resp[1].capitalize()
    resp[0] = resp[0].capitalize()
    resp = re.sub(r'(\.+)\s', r'\1', ' '.join(resp))
    # print(f"{msg = }")
    # return "shuffle_words(msg) = " + resp
    return resp


if __name__ == '__main__':
    # print(uwu("something something"))
    # print(uwu("Many years later, as he faced the firing squad, Colonel Aureliano Buendia was to remember that distant afternoon when his father took him to discover ice."))
    # print(derp(many_years))
    # print(uhm("Many years later, as he faced the firing squad, Colonel Aureliano Buendia was to remember that distant afternoon when his father took him to discover ice."*1))
    # print(uhm(""))
    # print(imdad("I'm tired..."))
    # print(re.sub())
    # print(shuffle_words(many_years))
    # print(shuffle_words("Foo foo, foo... Foo. Foo? Foo; foo foo foo's ... foo."))
    # print(shuffle_words("The quick, brown fox! Jumps over...the lazy dog?"))


    pass