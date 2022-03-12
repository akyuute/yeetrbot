import re
import random
import string
# from time import perf_counter
# from os import urandom

# $(eval
#     let rd;
#     let m = [/r|l/, /R|L/, /%20the%20/, /The/, /that/, /That/];
#     let s = ["w", "W", "%20teh%20", "De", "dat", "Dat"];
#     let q = "$(querystring)";
#     for (i in s) {
#         q = q.replace(RegExp(m[i], 'g'), s[i])
#     };
#     let r = decodeURIComponent(q).split('');
#     for (i = -1; i <= r.length; i++) {
#         rd = Math.random();
#         if ((r[i] == 'u') && (rd < 0.2)) {
#             r[i] = 'uwu'
#         } else if ((r[i] == 't') && (r[i + 1] == 'h') && (rd < 0.3)) {
#             r[i + 1] = ''
#         };
#         if ((/\s[a-z]/i.test(r[i] + r[i + 1]) || i == -1) && (rd < 0.1)) {
#             r[i + 1] = r[i + 1].toLowerCase() + "-" + r[i + 1];
#             i++
#         }
#     }
#     r.join('')) UwU

many_years = "Many years later, as he faced the firing squad, Colonel Aureliano Buendia was to remember that distant afternoon when his father took him to discover ice."

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

        def get_rand_index(max_size: int, previous_val: int, repeat_prob: float|int, min_size: int=0):
            """Returns a random integer with a specified probability that it differs from a previous value."""
            index = previous_val
            while min_size <= index == previous_val and repeat_prob < random.random():
                index = int(random.random() * max_size)
            return index

        for i, repl in enumerate(repls):
        # first, make unconditional replacements
            if isinstance(repl, list|tuple):
            # for replacements with multiple possible values,
            # we randomize which value gets chosen.
                rand_index = 0
                for _ in range(resp.count(matches[i])):
                    rand_index = get_rand_index(len(repl), rand_index, 0.2)
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


# print(uwu("something something"))
# print(uwu("Many years later, as he faced the firing squad, Colonel Aureliano Buendia was to remember that distant afternoon when his father took him to discover ice."))

# print(isinstance("2,3,4,5", tuple|list))
# print(hasattr((0,1,2), "__iter__"))
# print(hasattr(3, "__iter__"))
# deck = random.sample([1, 2, 3, 4, 5, 6, 7], 1)
# print(deck)

# print(urandom(10))
# print(random.SystemRandom.)




# $(eval
#     let up = Math.random() > 0.2;
#     let q = decodeURIComponent("$(querystring)").split(''); q.map(function(char) {
#         if (char == ' ') {
#             return " "
#         };
#         if (char == 'i' || char == 'I') {
#             return "i"
#         };
#         up = Math.random() > 0.2 ? !up : up;
#         return up ? char.toUpperCase() : char.toLowerCase()
#     }).join('')) o_O

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


# print(derp(many_years))



# $(eval
#     let match = /\s[a-z]/i;
#     let rand;
#     let q = "$(querystring)";
#     let r = decodeURIComponent(q).split('');
#     for (let i = -1; i < q.length; i++) {
#         rand = Math.random();
#         if ((match.test(r[i] + r[i + 1]) || i == -1) && (rand < 0.15)) {
#             r[i + 1] = r[i + 1] + "-" + r[i + 1];
#             i++
#         };
#         rand = Math.random();
#         if ((rand < 0.15) && (r[i] == ' ')) {
#             r[i] = '...'
#         } else if ((r[i] == ' ') && (rand < 0.3)) {
#             r[i] = ", uhm, "
#         }
#     }; r.join(''))...

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


# print(uhm("Many years later, as he faced the firing squad, Colonel Aureliano Buendia was to remember that distant afternoon when his father took him to discover ice."*1))
# print(uhm(""))


# try:
    # print(5/0)
# except ZeroDivisionError:
    # print("oooops")

# $(eval q = decodeURIComponent("$(querystring)").split(' '); r = q; m = [/\wer$/, /have/, /^yes/, /^no(?=\W)?$/, /did/, /^do$/, /you(?=\W)/, /you$/, /^my/, /your(?!e)/, /(there|that)(?=\W)?$/, /^are$/, /^the$/]; s = ["'er", 'Hast', 'Yea', 'Nay', 'Didst', 'Doth', 'Thee', 'Thou', 'Mine', 'Thine', 'Yonder', 'art', 'Ye'];
#     for (w in q) {
#         for (i in m) {
#             r[w] = r[w].replace(RegExp(m[i], 'i'), s[i])
#         };
#         Math.random() < 0.8 && (r[w] = r[w].replace(/(?<=\w),/, ", alas,")) || (r[w] = r[w].replace(/(e)?(?=\W?$)/, "eth"))
#     }; r.join(' ').replace(/it( is|'s)/gi, "'tis"))

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


# print(ye(""))


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

# print(imdad("I'm tired..."))
# print(re.sub())
4

def woahthere(msg: str):
    '''Returns one of several shocked reactions when someone uses mashing.'''
    pass