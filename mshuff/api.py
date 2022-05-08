"""
API request handling and processing
"""

from html import unescape
from urllib.parse import urlunparse

import json
import requests

from . import util


def open_session(credentials):
    """Return a session object with persistent credentials."""
    session = requests.Session()
    session.auth = tuple(credentials)
    session.headers.update({"User-agent":"Mozilla/5.0"})
    return session

def make_https(netloc, path):
    """Return a correctly formatted url string."""
    return urlunparse(("https", netloc, path, "", "", ""))

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

def query_url(session, url, path=None):
    """Wrapper for query_json that first fetches an API response."""
    content = session.get(url).content
    return query_json(content, path)

def get_where(content, key=lambda x : True, **kwargs):
    """Filter a list of json objects to those that match given key-value pairs."""
    filtered = []
    for item in content:
        if all(item[key] == value for key, value in kwargs.items()) and key(item):
            filtered.append(item)
    return filtered

def get_url(session, url, key = lambda x : True, **kwargs):
    """Wrapper for get_where that first fetches an API response."""
    content = query_url(session, url)
    return get_where(content, key = key, **kwargs)

def get_newest(content, lim=24, **kwargs):
    """Wrapper for get_where that returns the most recently uploaded item."""
    try:
        newest = min(get_where(content, **kwargs), key = lambda x : util.time_since(x["utime"]))
        if util.time_since(newest["utime"]) < lim:
            return newest
    except ValueError:
        return None
