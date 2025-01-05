import argparse
import json
import logging
import os
import subprocess
import sys
import tomllib

from logging import handlers
from pathlib import Path
from tomllib import TOMLDecodeError


class TtpException(Exception):
    pass


class Logger():
    def __init__(self):
        """
        Set up logging.
        """
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
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

    def parse(self, args: list):
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
            help=(
                "Override the episode of the TV show (if multiple, this is used as the starting "
                "episode number)"
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
            help="Override the season of the TV show"
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
            help="Override the year of the movie or TV show"
        )
        self.parser.add_argument("torrent_id")
        self.parser.add_argument("torrent_name")
        self.parser.add_argument("torrent_dir")
        self.parsed_args = self.parser.parse_args(args)
        self.format()

    def format(self):
        try:
            if self.parsed_args.episode:
                self.parsed_args.episode = int(self.parsed_args.episode)
            if self.parsed_args.season:
                self.parsed_args.season = int(self.parsed_args.season)
        except ValueError as e:
            logger.error(f"Can't convert value to int: {e}")
            sys.exit(1)


arg_handler = ArgHandler()


class ConfigHandler:
    def __init__(self):
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

    def load(self, path: str):
        try:
            with open(path, "rb") as f:
                try:
                    config = tomllib.load(f)
                    for key in self.config:
                        self.config[key] = {**self.config[key], **config[key]}
                except TOMLDecodeError as e:
                    logger.error(f"Could not decode config file at {path}: {e}")
                    sys.exit(1)
                # self.format()
        except FileNotFoundError as e:
            logger.error(f"Could not find config file at path {path}: {e}")
            sys.exit(1)

    # def format(self):
    #     """
    #     Ensures certain config items are formatted correctly.
    #     """
    #     try:
    #         self.config["extensions"]["video"] = (
    #             tuple(self.config["extensions"]["video"])
    #         )
    #         self.config["extensions"]["archive"] = (
    #             tuple(self.config["extensions"]["archive"])
    #         )
    #     except KeyError as e:
    #         logger.error(f"Missing required configuration option: {e}")
    #         sys.exit(1)


config_handler = ConfigHandler()


def extract_file(filename, dirname):
    command = ["7z", "e", f"-o{dirname}", f"{dirname}/{filename}"]
    subprocess.run(command)


def scan_dir(path: Path, depth: int, extensions: list[str]):
    depth -= 1
    with os.scandir(path) as it:
        for entry in it:
            entry_path = Path(entry)
            if entry_path.is_file() and entry_path.suffix in extensions:
                yield entry_path


def find_files(
    path: Path,
    extensions: list,
    depth: int = 1,
    max_files: int | None = None,
    min_files: int | None = None
):
    found_paths = []
    if path.is_file() and path.suffix in extensions:
        found_paths.append(path)
    elif path.is_dir():
        for result in scan_dir(path, depth, extensions):
            found_paths.append(result)
    # Check found files against max and min
    if max_files:
        if len(found_paths) > max_files:
            raise TtpException(f"Found {len(found_paths)} which is more than maximum {max_files}")
    if min_files:
        if len(found_paths) < min_files:
            raise TtpException(f"Found {len(found_paths)} which is less than minimum {min_files}")
    logger.debug(f"Found paths: {found_paths}")
    return found_paths
