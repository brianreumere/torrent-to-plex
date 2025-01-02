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
            logging.Formatter("%(processName)s[%(process)d]: %(levelname)s: %(message)s")
        )
        logger.addHandler(syslog_handler)
    # May be overriden later if the -v argument is used
    logger.setLevel("INFO")
    return logger


logger = setup_logger()

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)


def parse_args(parser: argparse.ArgumentParser, args: list):
    """
    Parse command-line arguments.

    :param argparse.ArgumentParser parser:
    :param list args:
    """
    parser.add_argument(
        "-c", "--config",
        action="store",
        default=str(Path.home() / ".config" / "ttp.toml"),
        help="Set the path to the config file"
    )
    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        default=False,
        help="Perform a dry run and show what actions would be taken"
    )
    parser.add_argument(
        "-l", "--links",
        action="store_true",
        default=True,
        help="Create hard links in the destination instead of copying files"
    )
    parser.add_argument(
        "-o", "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite files in the destination if they already exist"
    )
    parser.add_argument(
        "-t", "--title",
        action="store",
        help="Override the title of the movie or TV show"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose mode"
    )
    parser.add_argument("torrent_id")
    parser.add_argument("torrent_name")
    parser.add_argument("torrent_dir")
    return parser.parse_args(args)


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
