"""
API request handling and processing
"""

from html import unescape
from urllib.parse import urlparse, urlunparse

import json
import requests

from . import util


class Session(requests.Session):
    """Session object that caches unnecessary requests."""

    def __init__(self, root):
        """Store root url for relative requests."""
        self._root = root
        self._cache = {}
        super().__init__()

    def request(self, method, url, **kwargs):
        """Interpret incomplete urls as paths relative to the root, cache GET requests."""
        parsed = urlparse(url)
        if not all((parsed.scheme, parsed.netloc)):
            url = urlunparse(("https", self._root, url, "", "", ""))

        if method.upper() == "GET":
            if not url in self._cache:
                self._cache[url] = super().request(method, url, **kwargs)
            return self._cache[url]
        return super().request(method, url, **kwargs)

    def get_where(self, url, key=bool, **kwargs):
        """Return items from a GET json response filtered by a key function."""
        for i in self.get(url).json():
            if key(i) and all(i[a] == b for a, b in kwargs.items()):
                yield i

    def get_byage(self, url, lim=24, key=bool, **kwargs):
        """Wrapper for get_where that returns objects sorted by upload time."""
        for i in sorted(self.get_where(url, key, **kwargs), key=lambda x : x["utime"]):
            if util.time_since(i["utime"]) < lim and all:
                yield i
        yield None

def query_json(data, path=None):
    """Parse a string/byes into json, interpret a given path."""
    try:
        j = json.loads(data)
    except ValueError:
        j = json.loads(unescape(data))
    if path:
        for i in path.split("."):
            i = int(i) if i.isnumeric() else i
            j = j[i]
    return j

