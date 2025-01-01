import os
import PTN

from pathlib import Path
from torrent_to_plex.util import logger, extract_file


def get_movie_info(name: str, dir: str, config: dict, title: str | None = None):
    # Find movie and subtitles file
    subtitles_file = False
    subtitles_file_ext = False
    # Check if torrent is just a file
    if (
        Path(f"{dir}/{name}").is_file()
        and f"{dir}/{name}".endswith(config["extensions"]["video"])
    ):
        logger.debug(f"Found movie file at {dir}/{name}")
        movie_file = name
        movie_file_full_path = f"{dir}/{name}"
        movie_file_ext = Path(movie_file).suffix
    # Otherwise treat as a directory
    else:
        # Check for archive files and extract
        with os.scandir(f"{dir}/{name}") as it:
            for entry in it:
                if entry.name.endswith(config["extensions"]["archive"]) and entry.is_file():
                    archive_file = entry.name
                    extract_file(archive_file, f"{dir}/{name}")
        with os.scandir(f"{dir}/{name}") as it:
            for entry in it:
                # Find video files
                if entry.name.endswith(config["extensions"]["video"]) and entry.is_file():
                    movie_file = entry.name
                    movie_file_full_path = f"{dir}/{name}/{movie_file}"
                    movie_file_ext = Path(movie_file).suffix
                # Find subtitles
                if entry.name.endswith(".srt") and entry.is_file():
                    subtitles_file = entry.name
                    subtitles_file_ext = Path(subtitles_file).suffix
                elif os.path.isdir(f"{dir}/{name}/Subs"):
                    with os.scandir(f"{dir}/{name}/Subs") as subs:
                        for sub in subs:
                            if sub.name.endswith(".srt") and sub.is_file():
                                subtitles_file = f"Subs/{sub.name}"
                                subtitles_file_ext = Path(subtitles_file).suffix
                                break
    try:
        # Merge info from the directory name and file name
        movie_info = {**PTN.parse(movie_file), **PTN.parse(name)}
        if title:
            movie_info["title"] = title
        movie_title = movie_info["title"]
        movie_year = movie_info["year"]
    except KeyError:
        raise Exception(f"Couldn't get movie title and year! Movie info: {movie_info}")
    return {
        "title": movie_title,
        "year": movie_year,
        "full_path": movie_file_full_path,
        "ext": movie_file_ext,
        "subtitles_file": subtitles_file,
        "subtitles_file_ext": subtitles_file_ext
    }
