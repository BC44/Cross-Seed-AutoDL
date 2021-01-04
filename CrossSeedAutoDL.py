#!python3

import argparse
import json
import os
import re
import requests
import shutil
import time
from guessit import guessit
from string import Template
from urllib.parse import quote

parser = argparse.ArgumentParser(description='Searches for cross-seedable torrents')
parser.add_argument('-p', '--parse-dir', dest='PARSE_DIR', action='store_true', help='Will parse the items inside the input directory as individual releases')
parser.add_argument('-d', '--delay', metavar='DELAY', dest='DELAY', type=int, default=10, help='Pause duration (in seconds) between searches (default: 10)')
parser.add_argument('-i', '--input-path', metavar='INPUT_PATH', dest='INPUT_PATH', type=str, required=True, help='File or Folder for which to find a matching torrent')
parser.add_argument('-s', '--save-path', metavar='SAVE_PATH', dest='SAVE_PATH', type=str, required=True, help='Directory in which to store downloaded torrents')
parser.add_argument('-u', '--url', metavar='JACKETT_URL', dest='JACKETT_URL', type=str, required=True, help='URL for your Jackett instance, including port number if needed')
parser.add_argument('-k', '--api-key', metavar='API_KEY', dest='API_KEY', type=str, required=True, help='API key for your Jackett instance')
parser.add_argument('-t', '--trackers', metavar='TRACKERS', dest='TRACKERS', type=str, required=True, help='Tracker(s) on which to search. Comma-separates if multiple (no spaces)')
args = parser.parse_args()

if os.name == 'nt':
    from ctypes import windll, wintypes
    FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
    GetFileAttributes = windll.kernel32.GetFileAttributesW


class ReleaseData:
    @staticmethod
    def get_release_data(path):
        return {
            'main_path': path, 
            'basename': os.path.basename(path), 
            'size': ReleaseData._get_total_size(path), 
            'guessed_data': guessit( os.path.basename(path) )
        }

    @staticmethod
    def _get_total_size(path):
        if os.path.isfile(path):
            return ReleaseData._get_file_size(path)
        elif os.path.isdir(path):
            total_size = 0
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    filesize = ReleaseData._get_file_size(os.path.join(root, filename))
                    if filesize == None:
                        return None
                    total_size += filesize
            return total_size

    @staticmethod
    def _get_file_size(file_path):
        if ReleaseData._is_link(file_path):
            source_path = os.readlink(file_path)
            if os.path.isfile(source_path):
                return os.path.getsize(source_path)
            else:
                return None
        else:
            return os.path.getsize(file_path)

    @staticmethod
    def _is_link(file_path):
        if os.name == 'nt':
            if GetFileAttributes(file_path) & FILE_ATTRIBUTE_REPARSE_POINT:
                return True
            else:
                return False
        else:
            return os.path.islink(file_path)


class Searcher:
    search_url_template = Template( '$JACKETT_URL/api/v2.0/indexers/all/results?apikey=$API_KEY&Query=$SEARCH_STRING&Tracker%5B%5D=$TRACKERS' )
    # max size variance (in bytes) in order to account for extra or missing files, eg. nfo files
    size_variance = 5 * 1024**2
    # keep these keys in response json, discard the rest
    keys_from_result = ['Tracker', 'TrackerId', 'CategoryDesc', 'Title', 'Guid', 'Link', 'Details', 'Category', 'Size', 'Imdb', 'InfoHash']

    def __init__(self):
        self.search_results = []

    def search(self, local_release_data):
        search_string = local_release_data['guessed_data']['title']
        if local_release_data['guessed_data'].get('year', None) is not None:
            search_string += ' {}'.format( local_release_data['guessed_data']['year'] )

        search_string = quote(search_string)
        search_url = self.search_url_template.substitute(
            JACKETT_URL=args.JACKETT_URL.strip('/'), 
            API_KEY=args.API_KEY, 
            SEARCH_STRING=search_string, 
            TRACKERS=args.TRACKERS
        )

        # debug
        # print(search_url);exit()
        resp = requests.get(search_url)
        # debug
        # print( json.dumps(resp.json(), indent=4) );exit()
        self.search_results = resp.json()['Results']
        self._trim_results()

        return self._get_matching_results(local_release_data)

    def _get_matching_results(self, local_release_data):
        matching_results = []

        for result in self.search_results:
            # if torrent file is missing, ie. Blutopia
            if result['Link'] is None:
                continue
            if abs( result['Size'] - local_release_data['size'] ) <= self.size_variance:
                matching_results.append(result)

        # debug
        # self._save_results(local_release_data)
        return matching_results

    def _trim_results(self):
        for i, result in enumerate(self.search_results):
            final_result = {}
            for key in self.keys_from_result:
                final_result[key] = result[key]
            self.search_results[i] = final_result

    # some release name results in jackett get extra data appended in square brackets
    def _reformat_release_name(self, release_name):
        release_name_re = r'^(.+)( +\[.+\])?$'
        return re.search(release_name_re, release_name, re.IGNORECASE).group(1)

    # debug
    def _save_results(self, local_release_data):
        search_results_final = []
        for result in self.search_results:
            search_results_final.apend( {**result, 'guessed_data': guessit(result['Title'])} )

        with open('results.json', 'w', encoding='utf8') as f:
            json.dump(search_results_final, f, indent=4)

        with open('local_release_data.json', 'w', encoding='utf8') as f:
            json.dump(local_release_data, f, indent=4)


class Downloader:
    @staticmethod
    def download(result):
        release_name = Downloader._sanitize_name(result['Title'])
        file_path = os.path.join( args.SAVE_PATH, f'{release_name}.torrent' )
        file_path = Downloader._validate_path(file_path)

        download_url = result['Link']
        response = requests.get(download_url, stream=True)
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

    @staticmethod
    def _sanitize_name(release_name):
        release_name = re.sub('/', '-', release_name)
        release_name = re.sub(r'[^\w\-_.()\[\] ]+', '', release_name, flags=re.IGNORECASE)
        return release_name

    @staticmethod
    def _validate_path(file_path):
        filename, ext = os.path.splitext(file_path)

        n = 1
        while os.path.isfile(file_path):
            n += 1
            file_path = f'{filename} ({n}){ext}'

        return file_path


def main():
    assert_settings()
    paths = [ os.path.normpath(args.INPUT_PATH)] if not args.PARSE_DIR else [os.path.join(args.INPUT_PATH, f) for f in os.listdir(args.INPUT_PATH) ]

    for path in paths:
        local_release_data = ReleaseData.get_release_data('Jr Jr Good Old Days 2020')
        local_release_data['size'] = 5555
        if local_release_data['size'] is None:
            continue
        searcher = Searcher()
        matching_results = searcher.search(local_release_data)
        # debug
        [print(f['Title']) for f in matching_results]
        # for result in matching_results:
        #     Downloader.download(result)
        time.sleep(args.DELAY)
    

def assert_settings():
    assert os.path.exists(args.INPUT_PATH), f'"{args.INPUT_PATH}" does not exist'
    if args.PARSE_DIR:
        assert os.path.isdir(args.INPUT_PATH), f'"{args.INPUT_PATH}" is not a directory. The -p/--parse-dir flag will parse the contents within the input path as individual releases'
    assert os.path.isdir(args.SAVE_PATH), f'"{args.SAVE_PATH}" directory does not exist'

    assert args.JACKETT_URL.startswith('http'), 'Error: jackett URL must start with http / https'

    try:
        resp = requests.head(args.JACKETT_URL)
    except:
        print(f'"{args.JACKETT_URL}" cannot be reached')


if __name__ == '__main__':
    main()
