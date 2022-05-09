"""

███╗   ███╗ ██████╗██╗  ██╗██╗   ██╗███████╗███████╗
████╗ ████║██╔════╝██║  ██║██║   ██║██╔════╝██╔════╝
██╔████╔██║╚█████╗ ███████║██║   ██║█████╗  █████╗
██║╚██╔╝██║ ╚═══██╗██╔══██║██║   ██║██╔══╝  ██╔══╝
██║ ╚═╝ ██║██████╔╝██║  ██║╚██████╔╝██║     ██║
╚═╝     ╚═╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝

By Josh Davies

"""

import argparse
import logging
import os
import sys

from itertools import zip_longest

from . import api
from . import util
from . import playlist

def parse_args():
    """Parse the arguments passed to the script."""
    parser = argparse.ArgumentParser(description="Shuffle for the libretime API.")

    parser.add_argument("-u", metavar="url", type=str, required=True,
            help="Base URL of the target libretime instance, no scheme and no path.")

    parser.add_argument("-c", metavar=("user", "password"), nargs=2, type=str, required=True,
            help="Username and password of an account with API read/write access.")

    parser.add_argument("-n", metavar="int", default=1, type=int,
            help="Index to target in upcoming show list.")

    parser.add_argument("-q", action="store_true",
            help="Quiet mode, suppress output.")

    args = parser.parse_args()

    if args.q:
        logging.getLogger().disabled = True
        sys.stdout = sys.stderr = open(os.devnull, "w")

    return args

def format_content(position, file, playlist_url):
    """Format a playlist content payload from a file object."""
    return {
            "type": 0,
            "position": position,
            "trackoffset": 1.0,
            "cliplength": str(playlist.get_runtime([file])),
            "cuein": file["cuein"],
            "cueout": file["cueout"],
            "fadein": "00:00:00.500000",
            "fadeout": "00:00:00.500000",
            "playlist": playlist_url,
            "file": file["item_url"]
            }

def main():
    """Main script body."""
    args = parse_args()
    util.setup_logging()

    session = api.Session(args.u)
    session.auth = tuple(args.c)
    session.headers.update({"User-agent":"Mozilla/5.0"})

    logging.info("Requesting show info from %s.", args.u)
    show = api.query_json(session.get("/api/live-info-v2").content, f"shows.next.{args.n}")
    playlist_id = next(session.get_where("/api/v2/shows", id=show["id"]))["autoplaylist"]

    logging.info("Reading show config.")
    try:
        config = api.query_json(show["genre"])
    except ValueError:
        logging.error("Show %s contains no valid json in the genre field", show["name"])
        sys.exit()

    bulletin = []
    if config["bulletin"]:
        logging.info("Processing Bulletin")
        new = next(session.get_byage("/api/v2/files", track_type="BULLETIN"))
        if new:
            bulletin = [next(session.get_where("/api/v2/files", track_title="Bulletin Intro")), new]

    logging.info("Pooling valid tracks and jingles.")
    k = lambda x, a : util.common_keys(x, config[a])
    tracks = session.get_where("/api/v2/files", track_type="SONG", key = lambda x : k(x, "tracks"))
    sweeps = session.get_where("/api/v2/files", track_type="SWEEP", key = lambda x : k(x, "sweeps"))

    logging.info("Fitting to length.")
    tracks, sweeps = list(tracks), list(sweeps)
    length = util.parse_delta(show["ends"], show["starts"]) - playlist.get_runtime(bulletin)

    playlist.weighted_shuffle(tracks, lambda x : util.time_since(x["lptime"]))
    tracks = playlist.fit_runtime(tracks, length)

    sweeps = playlist.fit_runtime(sweeps, length - playlist.get_runtime(tracks), under=False)

    logging.info("Shuffling.")
    playlist.grouped_shuffle(tracks, "artist_name")

    logging.info("Querying existing content.")
    old_list = session.get_where("/api/v2/playlist-contents/", playlist = playlist_id)

    new_list = bulletin + util.even_merge(sweeps, tracks)
    for i, item in enumerate(new_list):
        new_list[i] = format_content(i, item, playlist_id)

    logging.info("Updating with %s of new content.", playlist.get_runtime(new_list))

    old_list = sorted(old_list, key = lambda x : x["position"])
    for old, new in zip_longest(old_list, new_list):
        if old and new:
            session.patch(old["item_url"], new)
        elif old and not new:
            session.delete(old["item_url"])
        else:
            session.post("/api/v2/playlist-contents/", new)

    session.patch(playlist_id, {"length": str(playlist.get_runtime(new_list, final=True))})

if __name__ == "__main__":
    main()
