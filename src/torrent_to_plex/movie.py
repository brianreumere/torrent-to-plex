from langcodes import Language
from pathlib import Path
from torrent_to_plex.torrent import Torrent
from torrent_to_plex.util import logger, config_handler


config = config_handler.config


class Movie(Torrent):
    def __init__(self, torrent_name: str, torrent_dir: str, overrides: dict):
        super().__init__(torrent_name, torrent_dir, overrides)
        self.videos = self.find_files(
            self.torrent_path,
            config["extensions"]["video"],
            max_files=1,
            min_files=1
        )

    def to_plex(self, library_path: Path, links: bool, overwrite: bool, dry_run: bool):
        for video in self.videos:
            path = video["path"]
            metadata = video["metadata"]
            plex_name = f"{metadata['title']} ({metadata['year']})"
            plex_folder_path = Path(library_path) / plex_name
            self.create_plex_dir(plex_folder_path, dry_run)
            plex_file_path = Path(plex_folder_path) / f"{plex_name}{path.suffix}"
            self.create_plex_file(
                path,
                plex_file_path,
                links,
                overwrite,
                dry_run
            )

        # Create subtitle files
        default_language_copied = False
        for subtitle in self.subtitles:
            subtitle_path = subtitle["path"]
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
