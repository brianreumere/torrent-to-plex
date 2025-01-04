import shutil
import sys

from pathlib import Path
from torrent_to_plex.movie import get_movie_info
from torrent_to_plex.tv import get_tv_eps
from torrent_to_plex.util import (
    logger,
    parser,
    parse_args,
    load_config
)


def main(argv=sys.argv):
    """
    Main function for the CLI app.

    :param list argv: Command-line arguments.
    """
    args = parse_args(parser, argv[1:])
    if args.verbose:
        logger.info("Verbose mode enabled, setting log level to DEBUG")
        logger.setLevel("DEBUG")
    logger.debug(f"Got arguments: {vars(args)}")
    logger.debug(f"Loading config from {args.config}")
    config = load_config(args.config)
    logger.debug(f"Got config: {config}")
    if args.torrent_dir == config["movies"]["src_dir"]:
        movie_info = get_movie_info(args.torrent_name, args.torrent_dir, config, title=args.title, year=args.year)
        # Create movie dir in destination
        dst_movie_dir = f"{config['movies']['dst_dir']}/{movie_info['title']} ({movie_info['year']})"
        if not args.dry_run:
            Path(dst_movie_dir).mkdir(exist_ok=True)
        else:
            logger.info(f"Would create directory {dst_movie_dir} but dry run is enabled")
        # Move movie and subtitles files (assume English) to destination
        if args.links:
            path = Path(
                f"{dst_movie_dir}/{movie_info['title']} ({movie_info['year']}){movie_info['ext']}"
            )
            if path.is_file() and args.overwrite and not args.dry_run:
                logger.info(f"Overwrite is enabled, deleting existing file at {path}")
                path.unlink()
            elif path.is_file() and args.overwrite and args.dry_run:
                logger.info(f"Overwrite is enabled, would delete existing file at {path} but dry run is also enabled")
            try:
                if path.is_dir():
                    print(f"{path.name} is a directory. This is unsupported.")
                    pass
                else:
                    if not args.dry_run:
                        path.hardlink_to(movie_info["full_path"])
                    else:
                        logger.info(f"Would create new link at {path} but dry run is enabled")
            except FileExistsError:
                print(f"{path.name} already exists.")
                pass
        else:
            if not args.dry_run:
                shutil.copyfile(
                    movie_info["full_path"],
                    f"{dst_movie_dir}/{movie_info['title']} ({movie_info['year']}){movie_info['ext']}"
                )
            else:
                logger.info("Dry run is enabled, skipping copy")
        if movie_info["subtitles_file"]:
            if args.links:
                path = Path(
                    (
                        f"{dst_movie_dir}/{movie_info['title']} "
                        f"({movie_info['year']}).en{movie_info['subtitles_file_ext']}"
                    )
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
                            path.hardlink_to(f"{args.torrent_dir}/{args.torrent_name}/{movie_info['subtitles_file']}")
                        else:
                            logger.info(f"Would create new link at {path} but dry run is enabled")
                except FileExistsError:
                    raise Exception(f"{path.name} already exists.")
            else:
                if not args.dry_run:
                    shutil.copyfile(
                        f"{args.torrent_dir}/{args.torrent_name}/{movie_info['subtitles_file']}",
                        (
                            f"{dst_movie_dir}/{movie_info['title']} "
                            f"({movie_info['year']}).en{movie_info['subtitles_file_ext']}"
                        )
                    )
                else:
                    logger.info("Dry run is enabled, skipping copy")
    elif args.torrent_dir == config["tv"]["src_dir"]:
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

if __name__ == "__main__":
    main()
