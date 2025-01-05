import json
import shutil
import sys

from pathlib import Path
from torrent_to_plex.movie import Movie, MovieException
from torrent_to_plex.tv import Tv, TvException
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
        except MovieException as e:
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
        except TvException as e:
            logger.error(f"Exception processing TV episode or season: {e}")
            return 1

        tv_eps = get_tv_eps(args.torrent_name, args.torrent_dir, config, title=args.title, year=args.year, season=args.season, episode=args.episode)
        if len(tv_eps) > 0:
            for ep in tv_eps:
                # Create show and season dirs in destination
                dst_tv_show_dir = f"{config['tv']['dst_dir']}/{ep['show']}"
                dst_tv_season_dir = f"{dst_tv_show_dir}/Season {ep['season']:02d}"
                try:
                    if not args.dry_run:
                        Path(dst_tv_show_dir).mkdir(exist_ok=True)
                    else:
                        logger.info(f"Would create directory {dst_tv_show_dir} but dry run is enabled")
                except FileExistsError:
                    # If dir exists just continue
                    pass
                try:
                    if not args.dry_run:
                        Path(dst_tv_season_dir).mkdir(exist_ok=True)
                    else:
                        logger.info(f"Would create directory {dst_tv_season_dir} but dry run is enabled")
                except FileExistsError:
                    # If dir exists just continue
                    pass
                if args.links:
                    path = Path(
                        f"{dst_tv_season_dir}/S{ep['season']:02d}E{ep['number']:02d}{ep['extension']}"
                    )
                    if path.is_file() and args.overwrite and not args.dry_run:
                        logger.info(f"Overwrite is enabled, deleting existing file at {path}")
                        path.unlink()
                    elif path.is_file() and args.overwrite and args.dry_run:
                        logger.info(f"Overwrite is enabled, would delete existing file at {path} but dry run is also enabled")
                    try:
                        if path.is_dir():
                            raise Exception(f"{path.name} is a directory. This is unsupported.")
                            pass
                        else:
                            if not args.dry_run:
                                path.hardlink_to(ep["file_path"])
                            else:
                                logger.info(f"Would create new link at {path} but dry run is enabled")
                    except FileExistsError:
                        raise Exception(f"{path.name} already exists.")
                else:
                    if not args.dry_run:
                        shutil.copyfile(
                            ep["file_path"],
                            f"{dst_tv_season_dir}/S{ep['season']:02d}E{ep['number']:02d}{ep['extension']}"
                        )
                    else:
                        logger.info("Dry run is enabled, skipping copy")
        else:
            raise Exception("No episodes found!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
