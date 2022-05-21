"""
Miscellaneous helper functions
"""

from string import punctuation
from datetime import datetime

import os
import logging
import sys

TIME_FMTS = "%H:%M", "%H:%M:%S", "%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"

def create_dir(directory):
    """Alias to make directories."""
    os.makedirs(directory, exist_ok=True)

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
