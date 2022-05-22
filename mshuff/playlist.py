"""
Functions for manipulating playlists: shuffles, sorts, etc
"""

import random
import os
import json

from datetime import timedelta
from collections import defaultdict, UserDict, deque

from .settings import CONF_DIR

from . import util
from . import settings

def load_config(name):
    """Load playlist config from file."""
    with open(os.path.join(CONF_DIR, f"{name}.json"), "r") as f:
        data = json.load(f)
    if "random" in data:
        return load_config(random.choice(data["random"]))
    return data

def get_content(config, tracks):
    """Yield from an array based on a playlist config."""

    def filter_content(tracks, category):
        """Filter based on an individual category."""
        eq = lambda a, b : a == b if category["exact"] else (a in b or b in a)
        queue, fields = deque(tracks), category["fields"]
        while len(queue) > 1:
            if all(eq(queue[0][a], b) if queue[0][a] else False for a, b in fields.items()):
                yield queue[0]
                queue.append(queue.popleft())
            else:
                queue.popleft()
        logging.error(f"No content found matching {config}")
        sys.exit(1)

    generators = [filter_content(tracks, i) for i in config["content"]]
    while True:
        yield next(random.choices(generators, k=1,
            weights=[i["weight"] for i in config["content"]])[0])

def get_runtime(files, final = False):
    """Calculate the true runtime of an iterable of file items."""
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

def fit_runtime(file_gen, target):
    """Draw from a generator of files to exceed a target length."""
    c = []
    while get_runtime(c) < target:
        c.append(next(file_gen))
    return c

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
