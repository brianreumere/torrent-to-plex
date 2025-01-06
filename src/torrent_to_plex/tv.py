from pathlib import Path
from torrent_to_plex.torrent import Torrent
from torrent_to_plex.util import config_handler


config = config_handler.config


class TvException(Exception):
    pass


class Tv(Torrent):
    def __init__(self, torrent_name: str, torrent_dir: str, overrides: dict):
        super().__init__(torrent_name, torrent_dir, overrides)
        self.videos = self.find_files(
            self.torrent_path,
            config["extensions"]["video"],
            depth=2  # To look in season directories for multi-season torrents
        )

    def to_plex(self, library_path: Path, links: bool, overwrite: bool, dry_run: bool):
        for video in self.videos:
            path = video["path"]
            metadata = video["metadata"]
            if "year" in metadata:
                plex_name = f"{metadata['title']} ({metadata['year']})"
            else:
                plex_name = metadata['title']
            plex_folder_path = Path(library_path) / plex_name
            self.create_plex_dir(plex_folder_path, dry_run)
            plex_season_path = Path(plex_folder_path) / f"Season {metadata['season']:02d}"
            self.create_plex_dir(plex_season_path, dry_run)
            plex_file_path = (
                Path(plex_season_path)
                / f"S{metadata['season']:02d}E{metadata['episode']:02d}{path.suffix}"
            )
            self.create_plex_file(
                path,
                plex_file_path,
                links,
                overwrite,
                dry_run
            )
