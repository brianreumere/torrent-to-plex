import argparse
import logging
import os
import sys
import tomllib

from collections.abc import Iterator
from logging import handlers
from pathlib import Path
from tomllib import TOMLDecodeError


class Logger():
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        stream_handler = logging.StreamHandler()
        self.logger.addHandler(stream_handler)
        if Path("/dev/log").exists():
            syslog_handler = handlers.SysLogHandler(address="/dev/log")
            # Include log level in messages to syslog
            syslog_handler.setFormatter(
                logging.Formatter("ttp[%(process)d]: %(levelname)s: %(message)s")
            )
            self.logger.addHandler(syslog_handler)
        # May be overriden later if the -v argument is used
        self.logger.setLevel("INFO")


logger = Logger().logger


class ArgHandler:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

    def parse(self, args: list) -> None:
        self.parser.add_argument(
            "-c", "--config",
            action="store",
            default=str(Path.home() / ".config" / "ttp.toml"),
            help="Set the path to the config file"
        )
        self.parser.add_argument(
            "-d", "--dry-run",
            action="store_true",
            default=False,
            help="Perform a dry run and show what actions would be taken"
        )
        self.parser.add_argument(
            "-e", "--episode",
            action="store",
            type=int,
            help=(
                "Override the episode of the TV show (if multiple, this is used as the starting "
                "episode number; no effect for movies)"
            )
        )
        self.parser.add_argument(
            "-l", "--links",
            action="store_true",
            default=True,
            help="Create hard links in the destination instead of copying files"
        )
        self.parser.add_argument(
            "-o", "--overwrite",
            action="store_true",
            default=False,
            help="Overwrite files in the destination if they already exist"
        )
        self.parser.add_argument(
            "-s", "--season",
            action="store",
            type=int,
            help="Override the season of the TV show (no effect for movies)"
        )
        self.parser.add_argument(
            "-t", "--title",
            action="store",
            help="Override the title of the movie or TV show"
        )
        self.parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose mode"
        )
        self.parser.add_argument(
            "-y", "--year",
            action="store",
            type=int,
            help="Override the year of the movie or TV show"
        )
        self.parser.add_argument("torrent_id")
        self.parser.add_argument("torrent_name")
        self.parser.add_argument("torrent_dir")
        self.parsed_args = self.parser.parse_args(args)


arg_handler = ArgHandler()


class ConfigHandler:
    def __init__(self) -> None:
        # Defaults
        self.config = {
            "movies": {},
            "tv": {},
            "extensions": {
                "video": [".mp4", ".mkv", ".avi"],
                "subtitle": [".srt"],
                "subtitle_default_language": ".en",
                "archive": [".rar"]
            }
        }

    def load(self, path: str) -> None:
        try:
            with open(path, "rb") as f:
                try:
                    config = tomllib.load(f)
                    for key in self.config:
                        self.config[key] = {**self.config[key], **config[key]}
                except TOMLDecodeError as e:
                    logger.error(f"Could not decode config file at {path}: {e}")
                    sys.exit(1)
        except FileNotFoundError as e:
            logger.error(f"Could not find config file at path {path}: {e}")
            sys.exit(1)


config_handler = ConfigHandler()


def scan_for_file_paths(path: Path, depth: int, extensions: list[str]) -> Iterator[Path]:
    depth -= 1
    with os.scandir(path) as it:
        for entry in it:
            entry_path = Path(entry)
            if entry_path.is_file() and entry_path.suffix in extensions:
                yield entry_path
