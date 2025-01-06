import json
import shutil
import sys

from pathlib import Path
from torrent_to_plex.movie import Movie
from torrent_to_plex.torrent import TorrentException
from torrent_to_plex.tv import Tv
from torrent_to_plex.util import (
    logger,
    arg_handler,
    config_handler
)


def main(argv=sys.argv):
    """
    Main function for the CLI app.

    :param list argv: Command-line arguments.
    """
    # Parse args
    arg_handler.parse(argv[1:])
    args = arg_handler.parsed_args

    if args.verbose:
        logger.info("Verbose mode enabled, setting log level to DEBUG")
        logger.setLevel("DEBUG")

    logger.debug(f"Got arguments: {json.dumps(vars(args))}")
    logger.debug(f"Loading config from {args.config}")

    # Load config
    config_handler.load(args.config)
    config = config_handler.config
    logger.debug(f"Got config: {json.dumps(config)}")

    if args.torrent_dir == config["movies"]["src_dir"]:
        try:
            movie = Movie(
                args.torrent_name,
                args.torrent_dir,
                overrides={
                    "title": args.title,
                    "year": args.year
                }
            )
            library_path = Path(config["movies"]["dst_dir"])
            movie.to_plex(library_path, args.links, args.overwrite, args.dry_run)
            return 0
        except TorrentException as e:
            logger.error(f"Exception processing movie: {e}")
            return 1
    elif args.torrent_dir == config["tv"]["src_dir"]:
        try:
            tv = Tv(
                args.torrent_name,
                args.torrent_dir,
                overrides={
                    "title": args.title,
                    "year": args.year,
                    "season": args.season,
                    "episode": args.episode
                }
            )
            library_path = Path(config["tv"]["dst_dir"])
            tv.to_plex(library_path, args.links, args.overwrite, args.dry_run)
            return 0
        except TorrentException as e:
            logger.error(f"Exception processing TV episode or season: {e}")
            return 1
    else:
        logger.error(f"Invalid directory {args.torrent_dir}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
