import os
import PTN

from pathlib import Path
from torrent_to_plex.util import logger, config_handler, find_files


class TvException(Exception):
    pass


class Tv:
    def __init__(self, torrent_name: str, torrent_dir: str, overrides: dict):
        config = config_handler.config
        self.torrent_name = torrent_name
        self.torrent_dir = torrent_dir
        self.torrent_path = Path(torrent_dir) / torrent_name
        self.video_paths = find_files(
            self.torrent_path,
            config["extensions"]["video"],
            depth=2
        )
        self.subtitle_paths = find_files(
            self.torrent_path,
            config["extensions"]["subtitle"],
            depth=2
        )
        self.get_metadata(overrides)


def get_tv_eps(name: str, dir: str, config: dict, title: str | None = None, year: str | None = None, season: str | None = None, episode: int | None = None):
    eps = []
    if os.path.isdir(f"{dir}/{name}"):
        # Check for archive files and extract
        with os.scandir(f"{dir}/{name}") as it:
            for entry in it:
                if entry.name.endswith(config["extensions"]["archive"]) and entry.is_file():
                    archive_file = entry.name
                    extract_file(archive_file, f"{dir}/{name}")
        with os.scandir(f"{dir}/{name}") as it:
            for entry in it:
                if entry.is_dir():
                    nested = os.scandir(f"{dir}/{name}/{entry.name}")
                    for nested_entry in nested:
                        ep_info = {**PTN.parse(name), **PTN.parse(nested_entry.name)}
                        # Override title if provided
                        if title:
                            ep_info["title"] = title
                        if year:
                            ep_info["year"] = year
                        if season:
                            ep_info["season"] = season
                        if episode:
                            ep_info["episode"] = episode
                        ep = {
                            "file_path": (
                                f"{dir}/{name}/{entry.name}/{nested_entry.name}"
                            ),
                            "extension": Path(nested_entry.name).suffix,
                            "season": ep_info["season"],
                            "number": ep_info["episode"],
                            "show": ep_info["title"]
                        }
                        logger.info(ep)
                        eps.append(ep)
                        if episode:
                            episode += 1
                    nested.close()
                elif entry.name.endswith(config["extensions"]["video"]) and entry.is_file():
                    ep_info = {**PTN.parse(name), **PTN.parse(entry.name)}
                    if title:
                        ep_info["title"] = title
                    if year:
                        ep_info["year"] = year
                    if season:
                        ep_info["season"] = season
                    if episode:
                        ep_info["episode"] = episode
                    ep = {
                        "file_path": f"{dir}/{name}/{entry.name}",
                        "extension": Path(entry.name).suffix,
                        "season": ep_info["season"],
                        "number": ep_info["episode"],
                        "show": ep_info["title"]
                    }
                    logger.info(ep)
                    eps.append(ep)
                    if episode:
                        episode += 1
                    # Don't look for subtitles since TV torrents generally don't
                    # have them?
    elif (
        os.path.isfile(f"{dir}/{name}")
        and f"{dir}/{name}".endswith(config["extensions"]["video"])
    ):
        ep_info = PTN.parse(name)
        if title:
            ep_info["title"] = title
        if year:
            ep_info["year"] = year
        if season:
            ep_info["season"] = season
        if episode:
            ep_info["episode"] = episode
        ep = {
            "file_path": f"{dir}/{name}",
            "extension": Path(f"{dir}/{name}").suffix,
            "season": ep_info["season"],
            "number": ep_info["episode"],
            "show": ep_info["title"]
        }
        logger.debug(f"Appending episode {ep}")
        eps.append(ep)
    else:
        raise Exception("Torrent path isn't a directory or a file!")
    logger.debug(f"Found {len(eps)} episodes")
    return eps
