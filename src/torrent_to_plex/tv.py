import os
import PTN

from pathlib import Path
from torrent_to_plex.util import logger, extract_file


def get_tv_eps(name: str, dir: str, config: dict, title: str | None = None, year: str | None = None, season: str | None = None):
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
                    nested.close()
                elif entry.name.endswith(config["extensions"]["video"]) and entry.is_file():
                    ep_info = {**PTN.parse(name), **PTN.parse(entry.name)}
                    ep = {
                        "file_path": f"{dir}/{name}/{entry.name}",
                        "extension": Path(entry.name).suffix,
                        "season": ep_info["season"],
                        "number": ep_info["episode"],
                        "show": ep_info["title"]
                    }
                    logger.info(ep)
                    eps.append(ep)
                    # Don't look for subtitles since TV torrents generally don't
                    # have them?
    elif (
        os.path.isfile(f"{dir}/{name}")
        and f"{dir}/{name}".endswith(config["extensions"]["video"])
    ):
        ep_info = PTN.parse(name)
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
