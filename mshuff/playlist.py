"""
Functions for manipulating playlists: shuffles, sorts, etc
"""

import random
from datetime import timedelta
from collections import defaultdict

from . import util


def get_runtime(files, final = False):
    """Calculate the true runtime of a list of file items."""
    runtime = timedelta()
    for i in [f for f in files if f is not None]:
        try:
            time = util.parse_delta(i["cueout"], i["cuein"])
            time -= timedelta(microseconds = time.microseconds % 1000)
            runtime += time
        except KeyError:
            continue
    if final:
        return runtime - timedelta(seconds=max(0, len(files)))
    return runtime - timedelta(seconds=max(0, len(files)-1))

def fit_runtime(files, target, under=True):
    """Trim a list of files just under/over a target length."""
    while get_runtime(files) < target:
        files = files+files
    for i, _ in enumerate(files):
        if under and get_runtime(files[0:i+1]) > target:
            files[i] = None
        if get_runtime(files[0:i+1]) > target:
            break
    return [i for i in files[0:i+1] if i is not None]

def weighted_shuffle(files, key = lambda x : x, x_lim = 4, y_lim = 4):
    """Pseudoshuffles a list of dictionaries prioritising weighted items."""

    def sigmoid(x):
        """Sigmoidal curve for weighting song selection."""
        x = min(max(0, x), x_lim-0.01)
        return y_lim / (1 + (x / (x_lim - x))**-3)

    files.sort(key = lambda x : random.random()**(1.0/sigmoid(key(x))))

def grouped_shuffle(files, field, jitter=0.1):
    """Pseudoshuffles a list of dictionaries maximising distance between groups."""
    groups = defaultdict(list)
    for i in files:
        groups[i[field]].append(i)

    for _, items in groups.items():
        spacing = 1/(len(items)+1)
        offset = random.uniform(0, spacing*2)
        for i, item in enumerate(items):
            item["sort"] = offset + i*spacing + random.uniform(-jitter, jitter)

    files.sort(key = lambda x : x["sort"])
