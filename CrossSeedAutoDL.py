#!python3

import argparse
import json
import os
import re
import requests
import shutil
from string import Template

parser = argparse.ArgumentParser(description='Searches for cross-seedable torrents')
parser.add_argument('-p', '--parse-dir', dest='PARSE_DIR', action='store_true', help='Indicates if input folder is the \
                    root folder for all downloaded content (eg. your torrent client download directory)')
parser.add_argument('-i', metavar='INPUT_PATH', dest='INPUT_PATH', type=str, required=True, help='File or Folder for which to find a matching torrent')
parser.add_argument('-s', '--save-path', metavar='SAVE_PATH', dest='SAVE_PATH', type=str, required=True, help='Directory in which to store downloaded torrents')
parser.add_argument('-u', '--url', metavar='JACKETT_URL', dest='JACKETT_URL', type=str, required=True, help='URL for your Jackett instance, including port number if needed')
parser.add_argument('-k', '--api-key', metavar='API_KEY', dest='API_KEY', type=str, required=True, help='API key for your Jackett instance')
parser.add_argument('-t', '--trackers', metavar='TRACKERS', dest='TRACKERS', type=str, required=True, help='Tracker(s) on which to search. Comma-separates if multiple (no spaces)')
args = parser.parse_args()

DOWNLOAD_HISTORY = []
DOWNLOAD_HISTORY_JSON = './DownloadHistory.json'
TITLES_NOT_FOUND_JSON = './TITLES_NOT_FOUND.json'
LOG_FILE = './SimpleLog.log'

SEARCH_URL_TEMPLATE = '$JACKETT_URL/api/v2.0/indexers/all/results?apikey=$API_KEY&Query=$SEARCH_STRING&Tracker%5B%5D=$TRACKERS'

AKA_DUAL_LANG_NAME_RE = r'(.+?)\baka\b(.+)'

TITLE_RE = r'(.+?)(\b(\d{4}|\d+p)\b|\b(season|s).?\d+)\b'
YEAR_RE = r'.+\b((?:19|20)\d\d)\b'
EDITION_RE = r'(tvdb.order|remaster|imax|proper|repack|internal|EXTENDED|UNRATED|DIRECTORS?|COLLECTORS?)(ed)?(.CUT)?'
GROUP_RE = r'- ?([^\.\s]+) *(\[.+?\])? *(\.\w+)?$'

OS_NAME = os.name

if OS_NAME == 'nt':
    from ctypes import windll, wintypes
    FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
    GetFileAttributes = windll.kernel32.GetFileAttributesW


def main():
    titlesNotFound = []
    # pathListings = os.listdir(MAIN_FOLDER)
    paths = [os.path.normpath(args.INPUT_PATH)] if not args.PARSE_DIR else [os.path.join(args.INPUT_PATH, f) for f in os.listdir(args.INPUT_PATH)]
    finalLogStr = ''

    loadDownloadHistory()

    # for i, listing in enumerate(pathListings):
    for i, path in enumerate(paths):
        # listingPath = os.path.join(MAIN_FOLDER, listing)
        path_basename = os.path.basename(path)

        group = getGroupName(path_basename)
        title = path_basename
        m = re.search(TITLE_RE, title, re.IGNORECASE)
        if m: title = m.group(1)

        year = ''
        m = re.search(YEAR_RE, path_basename)
        if m: year = m.group(1)

        title = re.sub(r'\'s\b', ' ', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+', ' ', title, flags=re.IGNORECASE)
        title = re.sub(EDITION_RE, ' ', title, flags=re.IGNORECASE)
        title = re.sub(r'[\W_]', ' ', title)

        # print(title)
        pathSize = get_size(path)
        if pathSize == None:
            continue

        queries = []
        if re.search(AKA_DUAL_LANG_NAME_RE, title, re.IGNORECASE):
            editedTitle = re.sub(AKA_DUAL_LANG_NAME_RE, r'\1', title, flags=re.IGNORECASE) + f' {year}'
            queries.append(editedTitle)
            editedTitle = re.sub(AKA_DUAL_LANG_NAME_RE, r'\2', title, flags=re.IGNORECASE) + f' {year}'
            queries.append(editedTitle)
        else:
            queries.append(f'{title} {year}')

        queries = [' '.join(f.split()) for f in queries]

        logStr = f'\n\nSearching for {i+1} of {len(paths)}:\t{queries}\t{[path_basename, pathSize]}\n'
        finalLogStr += logStr
        print(logStr)

        for query in queries:
            query = '%20'.join(query.split())
            # query = re.sub(r'\'', '%27', query)

            searchURL = Template(SEARCH_URL_TEMPLATE)
            searchURL = searchURL.substitute(JACKETT_URL=args.JACKETT_URL.strip('/'), API_KEY=args.API_KEY, SEARCH_STRING=query, TRACKERS=args.TRACKERS)
            source = requests.get(searchURL).text
            returnedJSON = json.loads(source)

            logStr = {f['Title']:f['Size'] for f in returnedJSON['Results']}
            finalLogStr += str(logStr) + '\n'
            print(logStr)

            found, announceDownloadings = findMatchingTorrent(returnedJSON, pathSize, path)
            finalLogStr += '\n'.join(announceDownloadings) + '\n'
            if found == False:
                titlesNotFound.append(path_basename)

            if i % 10 == 0 and i != 0 or i == len(paths) - 1:
                with open(LOG_FILE, 'w', encoding='utf8') as f:
                    f.write(finalLogStr)

    with open(TITLES_NOT_FOUND_JSON, 'w', encoding='utf8') as f:
        json.dump(titlesNotFound, f, indent=4)

    with open(DOWNLOAD_HISTORY_JSON, 'w', encoding='utf8') as f:
        json.dump(DOWNLOAD_HISTORY, f, indent=4)


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
    if OS_NAME == 'nt':
        if GetFileAttributes(filepath) & FILE_ATTRIBUTE_REPARSE_POINT:
            return True
        else:
            return False
    else:
        return os.path.islink(filepath)


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


def getGroupName(releaseName):
    m = re.search(GROUP_RE, releaseName)
    if m:
        return m.group(1)
    return ''


def findMatchingTorrent(returnedJSON, pathSize, listingPath):
    MB = 1000000
    MAX_FILESIZE_DIFFERENCE = 10 * MB
    announceDownloadings = []

    if os.path.isfile(listingPath) and pathSize < 1000 * MB:
        MAX_FILESIZE_DIFFERENCE = 0.01 * MB
    found = False
    for result in returnedJSON['Results']:
        listingTitle = result['Title']
        downloadURL = result['Link']
        listingSize = result['Size']

        torrent_listing_info = f'{result["Tracker"]}/{listingTitle}'

        # if size difference is less than the below referenced number of bytes, download torrent
        if abs(pathSize - listingSize) <= MAX_FILESIZE_DIFFERENCE:
            found = True
            if torrent_listing_info not in DOWNLOAD_HISTORY:
                print('\n  >> Found possible match. Downloading\n')
                announceDownloadings.append('\n  >> Found possible match. Downloading\n')
                DOWNLOAD_HISTORY.append(torrent_listing_info)
                downloadTorrent(downloadURL, listingTitle)
            else:
                print(f'\n  !> Torrent {listingTitle} already previously downloaded\n')
                announceDownloadings.append(f'\n  !> Torrent {listingTitle} already previously downloaded\n')
    return found, announceDownloadings


def downloadTorrent(downloadURL, torrentName):
    if OS_NAME == 'nt':
        torrentName = re.sub(r'[<>:\"/\\?*\|]+', '', torrentName)
    else:
        torrentName = re.sub('/', '-', torrentName)

    response = requests.get(downloadURL, stream=True)
    downloadPath = os.path.join(args.SAVE_PATH, f'{torrentName}.torrent')
    downloadPath = validatePath(downloadPath)

    with open(downloadPath, 'wb') as f:
        shutil.copyfileobj(response.raw, f)


def loadDownloadHistory():
    global DOWNLOAD_HISTORY
    try:
        with open(DOWNLOAD_HISTORY_JSON, 'r', encoding='utf8') as f:
            DOWNLOAD_HISTORY = json.load(f)
    except Exception:
        DOWNLOAD_HISTORY = []


if __name__ == '__main__':
    main()
