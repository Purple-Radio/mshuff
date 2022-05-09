"""
Miscellaneous helper functions
"""

from string import punctuation
from datetime import datetime

import logging
import sys

TIME_FMTS = "%H:%M", "%H:%M:%S", "%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"

def get_words(string_a):
    """Clean punctuation and make a string lowercase, then split into words."""
    return string_a.translate(str.maketrans('', '', punctuation)).lower().split(";")

def common_words(string_a, string_b):
    """Return true if strings contain common words."""
    words_a, words_b = get_words(string_a), get_words(string_b)
    try:
        return len(set(words_a).intersection(words_b)) > 0
    except TypeError:
        return False

def common_keys(dict_a, dict_b):
    """Return true if any matching keys contain common words."""
    dict_a, dict_b = strip_null(dict_a), strip_null(dict_b)
    for i in set(dict_a).intersection(set(dict_b)):
        if common_words(dict_a[i], dict_b[i]):
            return True
    return False

def strip_null(dict_a):
    """Strip key:value pairs with null values from dictionary."""
    return {a:b for a, b in dict_a.items() if b}

def even_merge(list_a, list_b):
    """Merge two lists together such that the elements are evenly spaced."""
    l, m , n = [], len(list_a), len(list_b)
    for i in range(m+n):
        q, r = divmod(i*n, m+n)
        l.append(list_a[i-q] if r < m else list_b[q])
    return l

def parse_time(timestring):
    """Convert an unespecified timestring to a datetime object."""
    for fmt in TIME_FMTS:
        try:
            return datetime.strptime(timestring, fmt)
        except ValueError:
            continue
    raise ValueError(f"Encountered non standard timestring: {timestring}")

def parse_delta(timestring_a, timestring_b):
    """Return time between two timestrings."""
    return abs(parse_time(timestring_a) - parse_time(timestring_b))

def time_since(timestring, scale=3600):
    """Returns the given timestring to the current system time, defaults to hours."""
    if isinstance(timestring, str):
        return (datetime.now() - parse_time(timestring)).total_seconds() / scale
    return 48

def setup_logging():
    """Initialise logging module config."""
    logging.basicConfig(format=("[%(levelname)s\033[0m] "
                                "\033[1;31m%(module)s\033[0m: "
                                "%(message)s"),
                        level = logging.INFO,
                        stream = sys.stdout)
