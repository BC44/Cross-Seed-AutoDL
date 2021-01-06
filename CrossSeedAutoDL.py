#!python3

import argparse
import json
import os
import re
import requests
import shutil
import time
from guessit import guessit
from urllib.parse import urlencode

parser = argparse.ArgumentParser(description='Searches for cross-seedable torrents')
parser.add_argument('-p', '--parse-dir', dest='PARSE_DIR', action='store_true', help='Will parse the items inside the input directory as individual releases')
parser.add_argument('-d', '--delay', metavar='DELAY', dest='DELAY', type=int, default=10, help='Pause duration (in seconds) between searches (default: 10)')
parser.add_argument('-i', '--input-path', metavar='INPUT_PATH', dest='INPUT_PATH', type=str, required=True, help='File or Folder for which to find a matching torrent')
parser.add_argument('-s', '--save-path', metavar='SAVE_PATH', dest='SAVE_PATH', type=str, required=True, help='Directory in which to store downloaded torrents')
parser.add_argument('-u', '--url', metavar='JACKETT_URL', dest='JACKETT_URL', type=str, required=True, help='URL for your Jackett instance, including port number if needed')
parser.add_argument('-k', '--api-key', metavar='API_KEY', dest='API_KEY', type=str, required=True, help='API key for your Jackett instance')
parser.add_argument('-t', '--trackers', metavar='TRACKERS', dest='TRACKERS', type=str, default=None, required=False, help='Tracker(s) on which to search. Comma-separated if multiple (no spaces). If ommitted, all trackers will be searched.')
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
    # max size difference (in bytes) in order to account for extra or missing files, eg. nfo files
    max_size_difference = 5 * 1024**2
    # keep these params in response json, discard the rest
    keys_from_result = ['Tracker', 'TrackerId', 'CategoryDesc', 'Title', 'Link', 'Details', 'Category', 'Size', 'Imdb']
    category_types = {'movie': 2000, 'episode': 5000}

    def __init__(self):
        self.search_results = []

    def search(self, local_release_data):
        search_query = local_release_data['guessed_data']['title']
        if local_release_data['guessed_data'].get('year', None) is not None:
            search_query += ' ' + str( local_release_data['guessed_data']['year'] )

        search_url = self._get_full_search_url(search_query, local_release_data)

        # debug
        # print(search_url);exit()
        resp = requests.get(search_url, local_release_data)
        # debug
        # print( json.dumps(resp.json(), indent=4) );exit()
        self.search_results = resp.json()['Results']
        self._trim_results()

        return self._get_matching_results(local_release_data)

    @staticmethod
    def _get_full_search_url(search_query, local_release_data):
        base_url = args.JACKETT_URL.strip('/') + '/api/v2.0/indexers/all/results?'

        main_params = {
            'apikey': args.API_KEY, 
            'Query': search_query
        }

        optional_params = {
            'Tracker[]': args.TRACKERS, 
            'Category[]': Searcher.category_types[ local_release_data['guessed_data']['type'] ], 
            'season': local_release_data['guessed_data'].get('season', None), 
            'episode': local_release_data['guessed_data'].get('episode', None)
        }

        for param, arg in optional_params.items():
            if arg is not None:
                main_params[param] = arg

        return base_url + urlencode(main_params)

    def _get_matching_results(self, local_release_data):
        matching_results = []
        # print(f'Parsing { len(self.search_results) } results. ', end='')

        for result in self.search_results:
            if abs( result['Size'] - local_release_data['size'] ) <= self.max_size_difference:
                matching_results.append(result)

        print(f'{ len(matching_results) } matched of { len(self.search_results) } results.')
        # debug
        self._save_results(local_release_data)
        return matching_results

    def _trim_results(self):
        url_re = r'^https?://[^/]+([^\s]+)'

        for i, result in enumerate(self.search_results):
            new_result = {}
            for key in self.keys_from_result:
                new_result[key] = result[key]
            new_result['Title'] = self._reformat_release_name( new_result['Title'] )
            self.search_results[i] = new_result

    # some release name results in jackett get extra data appended in square brackets
    def _reformat_release_name(self, release_name):
        release_name_re = r'^(.+?)( \[.*/.*\])?$'
        return re.search(release_name_re, release_name, re.IGNORECASE).group(1)

    # debug
    def _save_results(self, local_release_data):
        target_dict = {'local_release_data': local_release_data, 'results': self.search_results}
        # search_results_final = []
        # for result in self.search_results:
        #     search_results_final.apend( {**result, 'guessed_data': **local_release_data} )

        with open('results.json', 'w', encoding='utf8') as f:
            json.dump([target_dict], f, indent=4)

        # with open('local_release_data.json', 'w', encoding='utf8') as f:
        #     json.dump(local_release_data, f, indent=4)


class Downloader:
    @staticmethod
    def download(result):
        # if torrent file is missing, ie. Blutopia
        if result['Link'] is None:
            print( f'- Skipping release (no download link): {release_name}' )
            return

        release_name = Downloader._sanitize_name( '{} [{}]'.format( result['Title'], result['Tracker'] ) )
        file_path = os.path.join( args.SAVE_PATH, release_name + '.torrent' )
        file_path = Downloader._validate_path(file_path)

        print(f'- Grabbing release: {release_name}')

        response = requests.get(result['Link'], stream=True)
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

    for i, path in enumerate(paths):
        print(f'Searching for {i + 1} of { len(paths) }: { os.path.basename(path) } ', end='')

        local_release_data = ReleaseData.get_release_data(path)
        # local_release_data = ReleaseData.get_release_data('Jr Jr Good Old Days 2020')
        # local_release_data['size'] = 5555

        print( '/ {} {}'.format( local_release_data['guessed_data']['title'], local_release_data['guessed_data'].get('year', '') ) )

        if local_release_data['size'] is None:
            continue
        searcher = Searcher()
        matching_results = searcher.search(local_release_data)
        # debug
        # [print(f['Title']) for f in matching_results]
        for result in matching_results:
            Downloader.download(result)
        print('')
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
