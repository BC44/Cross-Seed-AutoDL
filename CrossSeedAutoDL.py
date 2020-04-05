import json
import os
import re
import requests
import PTN
import shutil
from ctypes import windll, wintypes

# path to download torrents into
DOWNLOAD_PATH = r''
# jackett api key
API_KEY = ''
# the parent folder whose child files/folders names will be used to conduct the search
MAIN_FOLDER = r''
# tracker (which has been added to your Jackett as an indexer) in which to search for cross-seedable torrents
TRACKER = ''
JACKETT_URL = 'http://127.0.0.1'
JACKETT_PORT = '9117'

TITLES_NOT_FOUND_JSON = './TITLES_NOT_FOUND.json'

SEARCH_STRING_START = '/api/v2.0/indexers/all/results?apikey='
SEARCH_STRING_MIDDLE = '&Query='
SEARCH_STRING_END = '&Tracker%5B%5D='

AKA_DUAL_LANG_NAME_RE = r'(.+?)\baka\b(.+)'

FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
GetFileAttributes = windll.kernel32.GetFileAttributesW


def main():
	titlesNotFound = []
	pathListings = [f for f in os.listdir(MAIN_FOLDER)]

	for i, listing in enumerate(pathListings):
		print(f'Searching for {i+1} of {len(pathListings)}: {os.path.basename(listing)}')

		listingPath = f'{MAIN_FOLDER}\\{listing}'

		pathSize = get_size(listingPath)
		if pathSize == None:
			continue

		info = PTN.parse(listing)
		title = info['title']
		title = re.sub(r'(-|\W+$)', ' ', title)
		year = info.get('year', '')

		queries = []
		if re.search(AKA_DUAL_LANG_NAME_RE, title, re.IGNORECASE):
			queries.append(re.sub(AKA_DUAL_LANG_NAME_RE, r'\1', title, flags=re.IGNORECASE))
			queries.append(re.sub(AKA_DUAL_LANG_NAME_RE, r'\2', title, flags=re.IGNORECASE))
		else:
			queries.append(title)

		for query in queries:
			query = f'{query} {year}' 
			query = '%20'.join(query.split())
			query = re.sub(r'\'', '%27', query)

			searchURL = f'{JACKETT_URL}:{JACKETT_PORT}{SEARCH_STRING_START}{API_KEY}{SEARCH_STRING_MIDDLE}{query}{SEARCH_STRING_END}{TRACKER}'
			source = requests.get(searchURL).text
			returnedJSON = json.loads(source)

			found = findMatchingTorrent(returnedJSON, pathSize)
			if found == False:
				titlesNotFound.append(listing)

	with open(TITLES_NOT_FOUND_JSON, 'w', encoding='utf8') as f:
		json.dump(titlesNotFound, f, indent=4)


def get_size(path):
	tempPath = path
	if os.path.isfile(path):
		return get_file_size(path)
	elif os.path.isdir(path):
		totalSize = 0
		for root, dirs, filenames in os.walk(path):
			for filename in filenames:
				filesize = get_file_size(os.path.join(root, filename))
				if filesize == None:
					return None
				totalSize += filesize
		return totalSize
	return None

def get_file_size(filepath):
	if islink(filepath):
		targetPath = os.readlink(filepath)
		if os.path.isfile(targetPath):
			return os.path.getsize(targetPath)
	else:
		return os.path.getsize(filepath)
	return None


def islink(filepath):
    # assert os.path.isdir(filepath), filepath
    if GetFileAttributes(filepath) & FILE_ATTRIBUTE_REPARSE_POINT:
        return True
    else:
        return False


def validatePath(filepath):
	path_filename, ext = os.path.splitext(filepath)
	n = 1

	if not os.path.isfile(filepath):
		return filepath

	filepath = f'{path_filename} ({n}){ext}'
	while os.path.isfile(filepath):
		n += 1
		filepath = f'{path_filename} ({n}){ext}'

	return filepath


def findMatchingTorrent(returnedJSON, pathSize):
	found = False
	for result in returnedJSON['Results']:
		listingTitle = result['Title']
		downloadURL = result['Link']
		listingSize = result['Size']

		# if size difference is less than the below referenced number of bytes, download torrent
		if abs(pathSize - listingSize) < 10 * 1000000:
			found = True
			print('  >> Found possible match. Downloading\n')
			downloadTorrent(downloadURL, listingTitle)
	return found


def downloadTorrent(downloadURL, torrentName):
	torrentName = re.sub(r'[<>:\"/\\?*\|]+', '', torrentName)

	response = requests.get(downloadURL, stream=True)
	projectedPath = os.path.join(DOWNLOAD_PATH, f'{torrentName}.torrent')
	downloadPath = validatePath(projectedPath)

	with open(downloadPath, 'wb') as f:
	    shutil.copyfileobj(response.raw, f)


if __name__ == '__main__':
	main()
