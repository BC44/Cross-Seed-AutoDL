# Cross-Seed-AutoDL
Finds cross-seedable torrents for Movies and TV via Jackett. Parses existing files/folders in order to download matching torrents.

Requires minimum python 3.6

Requires [Jackett](https://github.com/Jackett/Jackett)

Copy exact string for the tracker that appears in the torznab feed URL in Jackett to use for the script

![example img](https://i.ibb.co/8YdNh5v/image.png)


# Setup


Run `pip3 install -r requirements.txt` to install the required libraries


# Usage

	usage: CrossSeedAutoDL.py [-h] [-p] -i INPUT_PATH -s SAVE_PATH -u JACKETT_URL -k API_KEY -t TRACKERS

	Searches for cross-seedable torrents

	optional arguments:
	  -h, --help            show this help message and exit
	  -p, --parse-dir       Indicates if input folder is the root folder for multiple downloaded content (eg. your torrent
	                        client download directory)
      -d DELAY, --delay DELAY
                        Pause duration (in seconds) between searches (default: 10)
	  -i INPUT_PATH         File or Folder for which to find a matching torrent
	  -s SAVE_PATH          Directory in which to store downloaded torrents
	  -u JACKETT_URL, --url JACKETT_URL
	                        URL for your Jackett instance, including port number if needed
	  -k API_KEY, --api-key API_KEY
	                        API key for your Jackett instance
	  -t TRACKERS, --trackers TRACKERS
	                        Tracker(s) on which to search. Comma-separated if multiple (no spaces)

Examples:

Search for all items under a directory containing multiple downloaded content (include `-p` flag):

	py CrossSeedAutoDL.py -p -i "D:\TorrentClientDownloadDir\complete" -s "D:\DownloadedTorrents" -u "http://127.0.0.1:9117" -k "cb42579eyh4j11ht5sktjswq89t89q5t" -t blutopia

Search for a single item, a video file (omit `-p` flag)

	py CrossSeedAutoDL.py -i "D:\TorrentClientDownloadDir\complete\My.Movie.2010.720p.mkv" -s "D:\DownloadedTorrents" -u "http://127.0.0.1:9117" -k "cb42579eyh4j11ht5sktjswq89t89q5t" -t blutopia,passthepopcorn

Search for a single item, a season pack (omit `-p` flag)

	py CrossSeedAutoDL.py -i "D:\TorrentClientDownloadDir\complete\My.Show.Season.06.Complete" -s "D:\DownloadedTorrents" -u "http://127.0.0.1:9117" -k "cb42579eyh4j11ht5sktjswq89t89q5t" -t blutopia,broadcasthenet,morethantv