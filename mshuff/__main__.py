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

def get_config(show):
    """Process config for target show."""
    try:
        return api.query_json(show["genre"])
    except ValueError:
        logging.error("Show %s contains no valid json in the genre field", show["name"])
        sys.exit()

def get_bulletin(is_bulletin, files):
    """Generate bulletin intro."""
    if is_bulletin:
        newest = api.get_newest(files, track_type="BULLETIN", lim=24)
        if newest:
            return [api.get_where(files, track_title="Bulletin Intro")[0], newest]
    return []

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

def set_playlist(session, url, old_list, new_list):
    """Write new playlist content."""
    old_list = sorted(old_list, key = lambda x : x["position"])
    for old, new in zip_longest(old_list, new_list):
        if old and new:
            session.patch(old["item_url"], new)
        elif old and not new:
            session.delete(old["item_url"])
        else:
            session.post(api.make_https(url, "/api/v2/playlist-contents/"), new)
    session.patch(new_list[0]["playlist"],
            {"length": str(playlist.get_runtime(new_list, final=True))})

def main():
    """Main script body."""
    args = parse_args()
    util.setup_logging()

    s = api.open_session(args.c)

    logging.info("Requesting show info from %s.", args.u)
    show = api.query_url(s, api.make_https(args.u, "/api/live-info-v2"), f"shows.next.{args.n}")
    playlist_id = api.get_url(s, api.make_https(args.u, "/api/v2/shows"),
            id=show["id"])[0]["autoplaylist"]

    logging.info("Reading show config.")
    config = get_config(show)

    logging.info("Requesting file info from %s.", args.u)
    files = api.query_url(s, api.make_https(args.u, "/api/v2/files"))

    logging.info("Processing bulletin.")
    bulletin = get_bulletin(config["bulletin"], files)

    logging.info("Pooling valid tracks and jingles.")
    tracks = api.get_where(files, track_type="SONG",
            key=lambda x : util.any_common(config["tracks"], x["mood"]))

    sweeps = api.get_where(files, track_type="SWEEP",
            key=lambda x : util.any_common(config["sweepers"], x["mood"]))

    logging.info("Fitting to length.")
    length = util.parse_delta(show["ends"], show["starts"]) - playlist.get_runtime(bulletin)
    playlist.weighted_shuffle(tracks, lambda x : util.time_since(x["lptime"]))
    tracks = playlist.fit_runtime(tracks, length)
    sweeps = playlist.fit_runtime(sweeps, length - playlist.get_runtime(tracks), under=False)

    logging.info("Shuffling.")
    playlist.grouped_shuffle(tracks, "artist_name")
    new_list = bulletin + util.even_merge(sweeps, tracks)

    logging.info("Querying existing content.")
    old_list = api.get_url(s, api.make_https(args.u, "/api/v2/playlist-contents/"),
            playlist = playlist_id)

    new_list = bulletin + util.even_merge(sweeps, tracks)
    for i, item in enumerate(new_list):
        new_list[i] = format_content(i, item, playlist_id)

    logging.info("Updating with %s of new content.", playlist.get_runtime(new_list))

    set_playlist(s, args.u, old_list, new_list)

if __name__ == "__main__":
    main()
