# torrent-to-plex

`torrent-to-plex` is a Python CLI application that creates hard links or copies of completed movie or TV show torrents with the proper directory and file naming conventions for Plex.

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

You should be using the [Label and Execute plugins](https://deluge-torrent.org/plugins/) for Deluge. Manually label torrents as either TV or movies, and in label settings configure them to place completed torrents in different directories. Specify these directories in the `movie` and `tv` `src_dir` configuration parameters. Set the `dst_dir` values to the paths to your Plex movie and TV show libraries.

Once `torrent-to-plex` is installed (you can run `pip install git+https://github.com/brianreumere/torrent-to-plex` to install directly from Git), create an intermediary script to run the `ttp` command. For example, save the following as `ttp.sh`:

```bash
#!/bin/bash

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    printf "A required positional argument is missing!\\n"
    exit 1
fi

torrent_id="$1"
torrent_name="$2"
torrent_dir="$3"

ttp -v "$torrent_id" "$torrent_name" "$torrent_dir"
```

For other options you can pass to `ttp` run `ttp -h` or `ttp --help`.
