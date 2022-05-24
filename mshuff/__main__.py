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

from .settings import __version__, CONF_DIR

from . import settings
from . import api
from . import util
from . import playlist

def parse_args():
    """Parse the arguments passed to the script."""
    parser = argparse.ArgumentParser(description="Shuffle for the libretime API.")

    parser.add_argument("-u", metavar="url", type=str,
            help="Base URL of the target libretime instance, no scheme and no path.")

    parser.add_argument("-c", metavar=("user", "password"), nargs=2, type=str,
            help="Username and password of an account with API read/write access.")

    parser.add_argument("-n", metavar="int", default=1, type=int,
            help="Index to target in upcoming show list.")

    parser.add_argument("-q", action="store_true",
            help="Quiet mode, suppress output.")

    parser.add_argument("-v", action="store_true",
            help="Print version.")

    args = parser.parse_args()

    if args.v:
        parser.exit(0, f"mshuff {__version__}\n")

    if not args.c and not args.u:
        parser.error("-u and -c are required to establish connection.")

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
    util.create_dir(CONF_DIR)
    util.setup_logging()
    args = parse_args()

    session = api.Session(args.u)
    session.auth = tuple(args.c)
    session.headers.update({"User-agent":"Mozilla/5.0"})

    logging.info("Getting show info from %s.", args.u)
    show = session.get("/api/live-info-v2").json()["shows"]["next"][args.n]

    show_info = next(session.get_where("/api/v2/shows", id=show["id"]))
    show_id, playlist_id = show_info["item_url"], show_info["autoplaylist"]

    logging.info("Reading show config.")
    try:
        rewrite = show["genre"].startswith("r:")
        config = playlist.load_config(show["genre"].split(":")[-1])
    except FileNotFoundError:
        logging.error("Show %s contains no valid config name in the genre field", show["name"])
        sys.exit()

    logging.info("Writing playlist %s to show %s", config["name"], show["name"])

    bulletin = []
    if "bulletin" in config and config["bulletin"]:
        logging.info("Processing Bulletin")
        new = next(session.get_byage("/api/v2/files", track_type="BULLETIN"))
        if new:
            bulletin = [next(session.get_where("/api/v2/files", track_title="Bulletin Intro")), new]

    logging.info("Pooling valid tracks and jingles.")
    files = session.get("/api/v2/files").json()
    playlist.weighted_shuffle(files, lambda x : util.time_since(x["lptime"]))
    pool = playlist.get_content(config, files)

    logging.info("Fitting to length")
    length = util.parse_delta(show["ends"], show["starts"]) - playlist.get_runtime(bulletin)
    pool = playlist.fit_runtime(pool, length)

    logging.info("Separating out sweepers.")
    tracks = [i for i in pool if i["track_type"] == "SONG"]
    sweeps = [i for i in pool if i["track_type"] == "SWEEP"]

    if len(sweeps) > len(tracks)//2:
        logging.warning("Density of sweepers is greater than 1 per 2 tracks, check config.")

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

    logging.info("Updating playlist item metadata.")
    session.patch(playlist_id, {"length": str(playlist.get_runtime(new_list, final=True))})
    if rewrite and "name" in config:
        session.patch(show_id, {"name": config["name"]})
    if rewrite and "description" in config:
        session.patch(show_id, {"description": config["description"]})

if __name__ == "__main__":
    main()
