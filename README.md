This Repo is now archived. It was originally an experiment and a better tool has been created following the same idea for cross seeding.

Please see: [Cross-Seed](https://github.com/cross-seed/cross-seed) by `mmgoodnow`


# Cross-Seed-AutoDL
Finds cross-seedable torrents for Movies and TV via Jackett. Parses existing files/folders in order to download matching torrents.

Requires minimum python 3.6

Requires [Jackett](https://github.com/Jackett/Jackett)

Copy exact string for the tracker that appears in the torznab feed URL in Jackett to use for the script

![example img](https://i.ibb.co/8YdNh5v/image.png)


# Setup


Run `pip3 install -r requirements.txt` to install the required libraries


# Usage

	usage: CrossSeedAutoDL.py [-h] [-p] [-d delay] -i input_path -s save_path -u
	                          jackett_url -k api_key [-t trackers]
	                          [--ignore-history] [--strict-size]

	Searches for cross-seedable torrents

	optional arguments:
	  -h, --help            show this help message and exit
	  -p, --parse-dir       Optional. Indicates whether to search for the items inside
	                        the input directory as individual releases
	  -d delay, --delay delay
	                        Pause duration (in seconds) between searches (default:
	                        10)
	  -i input_path, --input-path input_path
	                        File or Folder for which to find a matching torrent
	  -s save_path, --save-path save_path
	                        Directory in which to store downloaded torrents
	  -u jackett_url, --url jackett_url
	                        URL for your Jackett instance, including port number
	                        if needed
	  -k api_key, --api-key api_key
	                        API key for your Jackett instance
	  -t trackers, --trackers trackers
	                        Tracker(s) on which to search. Comma-separated if
	                        multiple (no spaces). If ommitted, all trackers will
	                        be searched.
	  --ignore-history      Optional. Indicates whether to skip searches or downloads for files that have previously been searched/downloaded previously.
	  --strict-size         Optional. Indicates whether to match torrent search
	                        result sizes to exactly the size of the input path.


Examples:

If you're on Windows, use `py` like indicated below, otherwise replace `py` with `python3` if you're on Linux/Mac.

(include `-p` flag) Conducts multiple searches: Runs a search for each of the input directory's child items. ie. If input path is a season pack that contains 10 files, a search will be conducted for each file (10 total searches)

	py CrossSeedAutoDL.py -p -i "D:\TorrentClientDownloadDir\complete" -s "D:\DownloadedTorrents" -u "http://127.0.0.1:9117" -k "cb42579eyh4j11ht5sktjswq89t89q5t" -t blutopia

Search for a single item, a video file (omit `-p` flag)

	py CrossSeedAutoDL.py -i "D:\TorrentClientDownloadDir\complete\My.Movie.2010.720p.mkv" -s "D:\DownloadedTorrents" -u "http://127.0.0.1:9117" -k "cb42579eyh4j11ht5sktjswq89t89q5t" -t blutopia,passthepopcorn

Search for a single item, a season pack (omit `-p` flag)

	py CrossSeedAutoDL.py -i "D:\TorrentClientDownloadDir\complete\My.Show.Season.06.Complete" -s "D:\DownloadedTorrents" -u "http://127.0.0.1:9117" -k "cb42579eyh4j11ht5sktjswq89t89q5t" -t blutopia,broadcasthenet,morethantv
