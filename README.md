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
```

Optionally add the following to `~/.config/ttp.toml`. The defaults are shown below.

```ini
[extensions]
video = [ ".mp4", ".mkv", ".avi" ]
subtitle = [ ".srt" ]
subtitle_default_language = ".en"
archive = [ ".rar" ]
```

Subtitle files are found based on the file extensions in `subtitle`. If a found subtitle file matches does not have a [valid language code according to `langcodes`](https://github.com/georgkrause/langcodes?tab=readme-ov-file#checking-validity) it is assumed to be the the language in `subtitle_default_language`, and this value is used in the resulting filename copied to Plex. If there are multiple subtitle files without valid language codes, only the first is copied.

## Usage

You should be using the [Label and Execute plugins](https://deluge-torrent.org/plugins/) for Deluge.
