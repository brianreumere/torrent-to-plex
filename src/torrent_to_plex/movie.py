import json
import PTN
import shutil

from langcodes import Language
from pathlib import Path
from torrent_to_plex.util import logger, config_handler, find_files


class MovieException(Exception):
    pass


class Movie:
    def __init__(self, torrent_name: str, torrent_dir: str, overrides: dict):
        config = config_handler.config
        self.torrent_name = torrent_name
        self.torrent_dir = torrent_dir
        self.torrent_path = Path(torrent_dir) / torrent_name
        self.video_path = find_files(
            self.torrent_path,
            config["extensions"]["video"],
            max_files=1,
            min_files=1
        )[0]
        self.subtitle_paths = find_files(
            self.torrent_path,
            config["extensions"]["subtitle"]
        )
        self.get_metadata(overrides)

    def get_metadata(self, overrides: dict):
        try:
            # Remove None values from overrides
            overrides = {k: v for k, v in overrides.items() if v}
            # Prefer metadata from:
            #   1. Overrides
            #   2. Torrent name
            #   3. Video filename
            metadata = {
                **PTN.parse(self.video_path.name),
                **PTN.parse(self.torrent_name),
                **overrides
            }
            logger.debug(f"Got metadata: {json.dumps(metadata)}")
            self.title = metadata["title"]
            self.year = metadata["year"]
        except KeyError as e:
            raise MovieException(f"Failed to get metadata: {e}")

    @staticmethod
    def create_plex_movie_dir(path: Path, dry_run: bool):
        if path.exists():
            if not path.is_dir():
                raise MovieException(f"Path {path} exists and is not a directory")
        else:
            message = f"Creating directory {path}"
            if not dry_run:
                logger.debug(message)
                path.mkdir()
            else:
                logger.debug(f"DRY RUN: {message}")

    @staticmethod
    def create_plex_file(src_path, dst_path, links, overwrite, dry_run):
        if dst_path.exists():
            if not dst_path.is_file():
                raise MovieException(f"Path {src_path} exists and is not a file")
            elif overwrite:
                message = f"Deleting {dst_path} because overwrite is enabled"
                if not dry_run:
                    logger.debug(message)
                    dst_path.unlink()
                else:
                    logger.debug(f"DRY RUN: {message}")
            else:
                raise MovieException(f"Path {dst_path} already exists")
        if links:
            message = f"Creating hard link from {dst_path} to {src_path}"
            if not dry_run:
                logger.debug(message)
                dst_path.hardlink_to(src_path)
            else:
                logger.debug(f"DRY RUN: {message}")
        else:
            message = f"Copying {src_path} to {dst_path}"
            if not dry_run:
                logger.debug(message)
                shutil.copyfile(src_path, dst_path)
            else:
                logger.debug(f"DRY RUN: {message}")

    def to_plex(self, library_path: Path, links: bool, overwrite: bool, dry_run: bool):
        config = config_handler.config
        plex_name = f"{self.title} ({self.year})"
        plex_folder_path = Path(library_path) / plex_name
        plex_file_path = Path(plex_folder_path) / f"{plex_name}{self.video_path.suffix}"

        # Create movie directory
        self.create_plex_movie_dir(plex_folder_path, dry_run)

        # Create video file
        self.create_plex_file(
            self.video_path,
            plex_file_path,
            links,
            overwrite,
            dry_run
        )

        # Create subtitle files
        default_language_copied = False
        for subtitle_path in self.subtitle_paths:
            valid_language_code = False
            default_language = False
            subtitle_suffix = subtitle_path.suffix
            language_suffix = subtitle_path.suffixes[-2]
            if Language.get(language_suffix).is_valid():
                valid_language_code = True
                logger.debug(f"Found valid language suffix {language_suffix} in {subtitle_path}")
                plex_subtitle_path = (
                    Path(plex_folder_path)
                    / f"{plex_name}{language_suffix}{subtitle_suffix}"
                )
            else:
                default_language = True
                default_language_suffix = config['extensions']['subtitle_default_language']
                logger.debug(
                    f"No valid language found in {subtitle_path}, assuming default "
                    f"{default_language_suffix}"
                )
                plex_subtitle_path = (
                    Path(plex_folder_path)
                    / f"{plex_name}{default_language_suffix}{subtitle_suffix}"
                )
            if (
                (default_language and not default_language_copied)
                or valid_language_code
            ):
                self.create_plex_file(
                    subtitle_path,
                    plex_subtitle_path,
                    links,
                    overwrite,
                    dry_run
                )
                if default_language:
                    default_language_copied = True
