import json
import PTN
import shutil

from pathlib import Path
from torrent_to_plex.util import logger, config_handler, scan_for_file_paths


config = config_handler.config


class TorrentException(Exception):
    pass


class Torrent:
    def __init__(self, torrent_name: str, torrent_dir: str, overrides: dict):
        self.torrent_name = torrent_name
        self.torrent_dir = torrent_dir
        self.overrides = overrides
        self.torrent_path = Path(torrent_dir) / torrent_name
        self.subtitles = self.find_files(
            self.torrent_path,
            config["extensions"]["subtitle"],
            metadata=False
        )

    def find_files(
        self,
        path: Path,
        extensions: list,
        depth: int = 1,
        max_files: int | None = None,
        min_files: int | None = None,
        metadata: bool = True
    ):
        files = []
        if path.is_file() and path.suffix in extensions:
            files.append({"path": path})
        elif path.is_dir():
            for file_path in scan_for_file_paths(path, depth, extensions):
                files.append({"path": file_path})
        # Check found files against max and min if they're set
        if max_files:
            if len(files) > max_files:
                raise TorrentException(
                    f"Found {len(files)} which is more than maximum {max_files}"
                )
        if min_files:
            if len(files) < min_files:
                raise TorrentException(
                    f"Found {len(files)} which is less than minimum {min_files}"
                )
        if metadata:
            logger.debug(f"Getting metadata for paths: {files}")
            for file in files:
                file["metadata"] = self.get_metadata(
                    self.torrent_name,
                    file["path"].name,
                    self.overrides
                )
            logger.debug(f"Returning files with metadata: {files}")
        return files

    @staticmethod
    def get_metadata(torrent_name, filename, overrides: dict):
        try:
            # Remove None values from overrides
            overrides = {k: v for k, v in overrides.items() if v}
            # Prefer metadata from:
            #   1. Overrides
            #   2. Video filename
            #   3. Torrent name
            metadata = {
                **PTN.parse(torrent_name),
                **PTN.parse(filename),
                **overrides
            }
            logger.debug(f"Got metadata: {json.dumps(metadata)}")
            return metadata
        except KeyError as e:
            raise TorrentException(f"Failed to get metadata: {e}")

    @staticmethod
    def create_plex_dir(path: Path, dry_run: bool):
        if path.exists():
            if not path.is_dir():
                raise TorrentException(f"Path {path} exists and is not a directory")
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
                raise TorrentException(f"Path {src_path} exists and is not a file")
            elif overwrite:
                message = f"Deleting {dst_path} because overwrite is enabled"
                if not dry_run:
                    logger.debug(message)
                    dst_path.unlink()
                else:
                    logger.debug(f"DRY RUN: {message}")
            else:
                raise TorrentException(f"Path {dst_path} already exists")
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
