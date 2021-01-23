# Cross-Seed-AutoDL
Finds cross-seedable torrents for Movies and TV via Jackett. Parses existing files/folders in order to download matching torrents.

Requires minimum python 3.6

Requires [Jackett](https://github.com/Jackett/Jackett)

Copy exact string for the tracker that appears in the torznab feed URL in Jackett to use for the script

![example img](https://i.ibb.co/8YdNh5v/image.png)


# Setup


Run `pip3 install -r requirements.txt` to install the required libraries


# Usage

	usage: CrossSeedAutoDL.py [-h] [-p] [-d delay] -i input_path -s save_path -u jackett_url -k api_key [-t trackers]
	                          [--ignore-history]

	Searches for cross-seedable torrents

	optional arguments:
	  -h, --help            show this help message and exit
	  -p, --parse-dir       Optional. Indicates whether to parse the items inside the input directory as individual releases
	  -d delay, --delay delay
	                        Pause duration (in seconds) between searches (default: 10)
	  -i input_path, --input-path input_path
	                        File or Folder for which to find a matching torrent
	  -s save_path, --save-path save_path
	                        Directory in which to store downloaded torrents
	  -u jackett_url, --url jackett_url
	                        URL for your Jackett instance, including port number if needed
	  -k api_key, --api-key api_key
	                        API key for your Jackett instance
	  -t trackers, --trackers trackers
	                        Tracker(s) on which to search. Comma-separated if multiple (no spaces). If ommitted, all trackers will
	                        be searched.
	  --ignore-history      Optional. Indicates whether to ignore history file when conducting searches (for re-downloads)

Examples:

Search for all items under a directory containing multiple downloaded content (include `-p` flag):

	py CrossSeedAutoDL.py -p -i "D:\TorrentClientDownloadDir\complete" -s "D:\DownloadedTorrents" -u "http://127.0.0.1:9117" -k "cb42579eyh4j11ht5sktjswq89t89q5t" -t blutopia

Search for a single item, a video file (omit `-p` flag)

	py CrossSeedAutoDL.py -i "D:\TorrentClientDownloadDir\complete\My.Movie.2010.720p.mkv" -s "D:\DownloadedTorrents" -u "http://127.0.0.1:9117" -k "cb42579eyh4j11ht5sktjswq89t89q5t" -t blutopia,passthepopcorn

Search for a single item, a season pack (omit `-p` flag)

	py CrossSeedAutoDL.py -i "D:\TorrentClientDownloadDir\complete\My.Show.Season.06.Complete" -s "D:\DownloadedTorrents" -u "http://127.0.0.1:9117" -k "cb42579eyh4j11ht5sktjswq89t89q5t" -t blutopia,broadcasthenet,morethantv