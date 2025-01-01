# torrent-to-plex

A Python script that creates hard links or copies of completed movie or TV show torrents with the proper directory and file naming conventions for Plex.

## Configuration

Place the following in `~/.config/ttp.toml`.

```ini
[movies]
src_dir = "/mnt/Media/Torrents/Complete/Movies"
dst_dir = "/mnt/Media/Movies"
[tv]
src_dir = "/mnt/Media/Torrents/Complete/TV"
dst_dir = "/mnt/Media/TV"
[extensions]
video = [ ".mp4", ".mkv", ".avi" ]
archive = [ ".rar" ]
```

## Usage

This script assumes you are using the [Label and Execute plugins](https://deluge-torrent.org/plugins/) for Deluge.


