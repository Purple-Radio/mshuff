"""
Miscellaneous helper functions
"""

from datetime import datetime
import logging
import sys


TIME_FMTS = "%H:%M", "%H:%M:%S", "%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"

def any_common(list_a, list_b):
    """Return true if lists/strings contain common items."""
    list_a = list_a.split() if isinstance(list_a, str) else list_a
    list_b = list_b.split() if isinstance(list_b, str) else list_b
    try:
        return len(set(list_a).intersection(list_b)) > 0
    except TypeError:
        return False

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
    return (datetime.now() - parse_time(timestring)).total_seconds() / scale

def setup_logging():
    """Initialise logging module config."""
    logging.basicConfig(format=("[%(levelname)s\033[0m] "
                                "\033[1;31m%(module)s\033[0m: "
                                "%(message)s"),
                        level = logging.INFO,
                        stream = sys.stdout)
