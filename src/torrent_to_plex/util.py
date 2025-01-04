import argparse
import logging
import subprocess
import sys
import tomllib

from logging import handlers
from pathlib import Path
from tomllib import TOMLDecodeError


def setup_logger():
    """
    Set up logging.
    """
    logger = logging.getLogger(__name__)
    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)
    if Path("/dev/log").exists():
        syslog_handler = handlers.SysLogHandler(address="/dev/log")
        # Include log level in messages to syslog
        syslog_handler.setFormatter(
            logging.Formatter("ttp[%(process)d]: %(levelname)s: %(message)s")
        )
        logger.addHandler(syslog_handler)
    # May be overriden later if the -v argument is used
    logger.setLevel("INFO")
    return logger


logger = setup_logger()


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


def load_config(path: str):
    try:
        with open(path, "rb") as f:
            try:
                config = tomllib.load(f)
                try:
                    config["extensions"]["video"] = tuple(config["extensions"]["video"])
                    config["extensions"]["archive"] = tuple(config["extensions"]["archive"])
                except KeyError as e:
                    logger.error(f"Missing required configuration option: {e}")
                    sys.exit(1)
                return config
            except TOMLDecodeError as e:
                logger.error(f"Could not decode config file at {path}: {e}")
                sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"Could not find config file at path {path}: {e}")
        sys.exit(1)


def extract_file(filename, dirname):
    command = ["7z", "e", f"-o{dirname}", f"{dirname}/{filename}"]
    subprocess.run(command)
