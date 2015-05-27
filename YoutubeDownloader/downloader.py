import config
import os

import re
import requests


def find_and_download(song, CLIENT_ID=None):
    if config.CLIENT_ID == None and not CLIENT_ID:
        print 'Please set your CLIENT_ID in {0}'.format(
              '/'.join(os.path.realpath(__file__).split('/')[:-1]))
        exit(1)

    if exists(song['title']):
        print "{0} already exists!".format(song['title'])
        return

    unfiltered_results = get_results(song)
    filtered_results = filter_results(song, unfiltered_results)
    vid_ids = order_results(song, filtered_results)
    if not vid_ids:
        song['title'] = re.sub('\(.+\)', '', song['title'])
        unfiltered_results = get_results(song)
        filtered_results = filter_results(song, unfiltered_results)
        vid_ids = order_results(song, filtered_results)
        if not vid_ids:
            # missing.write(song['artist'] + ' --- ' + song['title'] + '\n')
            return
    for vid_id in vid_ids:
        if exists(song['title']) or exists(vid_id):
            print "{0} already exists!".format(song['title'])
            return
        print "Downloading {0}...".format(song['title'])
        download_song(vid_id, song)
        remove_m4a(vid_id)


def download_song(vid_id, song):
    """Downloads a song's audio content via youtube-dl.

    @arg: video_id: ID for the video's audio to download.
    """
    try:
    # We're lazy. Shell out to youtube-dl.
        s = ('youtube-dl --extract-audio --no-mtime '
                  '--audio-quality=0 --audio-format=mp3 --add-metadata '
                  ' -o "' + song['artist'].strip() + ' - '
                  '' + song['title'] + '.%(ext)s" '
                  '"http://www.youtube.com/watch?v={0}"'
                  .format(vid_id))
        os.system(s)
    except:
        print "Exception happened."
        return True
        # Strip out the crap that youtube-dl puts on the end, or figure out
        # which option doesn't include it.


def get_results(song):
    params = config.DEFAULT_PARAMS
    params['part'] = 'snippet,id'
    params['maxResults'] = 50
    params['q'] = '{0} - {0}'.format(song['artist'], song['title'])
    url = config.BASE_URL.format('search')
    results = requests.get(url, params=params).json()['items']
    statted_results = get_extra_stats(results)
    return statted_results


def get_extra_stats(results):
    filtered_results, ids = [], []
    for result in results:
        vid_id = result['id'].get('videoId')
        if vid_id:
            filtered_results.append(result)
            ids.append(vid_id)
    params = config.DEFAULT_PARAMS
    params['part'] = 'contentDetails,statistics'
    params['id'] = ','.join(ids),
    params['maxResults'] = 50
    url = config.BASE_URL.format('videos')
    stats = requests.get(url, params=params).json()['items']
    for i, item in enumerate(stats):
        filtered_results[i]['contentDetails'] = item['contentDetails']
        filtered_results[i]['statistics'] = item['statistics']
    return filtered_results


def order_results(song, results):
    """Finds the best matching song for a query.

    @arg: song: Song dictionary with title and other info.
    """
    # results = self.get_song_results(song, specs, hd=True)

    # Filter HD results on number of views
    # results = filter(
    #     lambda x: x['views'] > self.MIN_HD_VIEWS,
    #     results
    # )
    # Get the normal results again.
    num_results = len(results)
    for result in results:
        result['similar'] = len(filter(
            lambda x: is_similar(result['duration'], x['duration']),
            results)
        )

    # Check that there are > 30% matches for similar times.
    filtered_results = filter(
        lambda x: x['similar'] > int(num_results * .3),
        results
    )
    if not filtered_results:
        # Give the results a chance.
        filtered_results = filter(
            lambda x: x['similar'] > int(num_results * .2),
            results
        )

    # Filter based on number of views.
    filtered_results = filter(
        lambda x: x['views'] > config.MIN_VIEWS,
        filtered_results
    )

    # Check for HD
    hd_results = set(
        [(x['video_id'], x['views']) for x in filtered_results
            if x['hd'] == 'true']
    )

    whitelisted_results = set(
        [(x['video_id'], x['views']) for x in filtered_results
            if x['priority']]
    )

    preferred_results = hd_results.intersection(whitelisted_results)
    remaining_results = [
        (x['video_id'], x['views']) for x in filtered_results
    ]

    all_results = [preferred_results, hd_results, whitelisted_results,
                   remaining_results]

    # Sort by number of views.
    results = []
    for l in all_results:
        results.extend([x[0] for x in
                        list(reversed(sorted(
                            [x for x in l if x not in all_results],
                                key=lambda x: x[1]))
                        )])

    if results:
        return results
    else:
        print ("Could not find reliable song for query: {0}!"
               .format(song['title']))
        return None


def filter_results(song, results):
    """
    TODO Ideas:
        1. Check to see the ratio of views to likes to better assess priority
        2. Check to see the ratio of likes to dislikes to better assess priortyu
    """
    new_results = []
    for result in results:
        valid, priority = is_valid(song, result)
        if valid:
            duration = parse_duration(result['contentDetails']['duration'])
            new_results.append({
                'title': song['title'],
                'video_id': result['id']['videoId'],
                'duration': duration,
                'similar': 0,
                'hd': False,  # TODO add in hd filters
                'priority': priority,
                'views': result['statistics']['viewCount']
            })
    return new_results


def is_valid(song, result):
    title = clean(song['title'].strip(' ').lower().decode('utf8')).replace(', ', ',')
    artist = clean(song['artist'].strip(' ').lower().decode('utf8')).replace(', ', ',')
    yt_title = clean(result['snippet']['title'].lower()).replace(', ', ',')
    query = '{0} {1}'.format(title, artist)

    # Songs will likely never be less than 2:20 that I am searching for.
    duration = parse_duration(result['contentDetails']['duration'])
    if duration < 140:
        return False, False

    # Do our weird checking thing.
    # Magic.
    for word in yt_title.split(' '):
        for l in config.BLACKLIST:
            for illegal_word in l:
                if illegal_word in word and illegal_word not in query:
                    for similar in l:
                        if similar in title:
                            break
                    else:
                        return False, False
                    break

    if (not all([word in yt_title for word in title]) and
            not all([word in yt_title for word in artist])):
        return False, False

    for phrase in config.PRIORITY:
        if phrase in yt_title:
            return True, True
    return True, False


def is_similar(duration1, duration2):
    """Determines if two durations are similar.

    Similarity is defined in your __init__, or can
    be provided manually.

    @arg: duration1: Duration to compare to.
    @arg: duration2: Duration to compare to.
    """
    lower = duration1 - duration1 * config.SIMILARITY
    higher = duration1 + duration1 * config.SIMILARITY
    return lower <= duration2 and duration2 <= higher


def parse_duration(dur_string):
    """
    @arg: dur_string: Formatted `PT<Hour>H<Min>M<Seconds>S`
    If the duration (in hours, minutes, or seconds) does not need to be
    represented then it won't.
    """
    hours, mins, secs = 0, 0, 0
    dur_string = dur_string[2:]  # Remove the PT from beginning of string
    hour_split = dur_string.split('H')
    if len(hour_split) == 2:
        hours = int(hour_split[0])
        hour_split = hour_split[1]
    min_split = ''.join(hour_split).split('M')
    if len(min_split) == 2:
        mins = int(min_split[0])
        min_split = min_split[1]
    sec_split = ''.join(min_split).split('S')
    if len(sec_split) > 1:
        secs = int(sec_split[0])
    return hours * 60 * 60 + mins * 60 + secs


def clean(string):
    """Cleans a string of all characters we wish to ignore.

    @arg: string: String to clean
    """
    return reduce(lambda original, ignore: original.replace(ignore, ''),
                  [string] + config.IGNORE_CHARACTERS)


def exists(title=None, ytid=None, target='.'):
    """Checks to see if a song was downloaded.

    TODO: Find a more optimized way of doing this.

    @arg: title: Song title
    @arg: ytid: Youtube id of song
    @arg: target: Target directory
    """
    if not title:
        title = ytid
    title = clean(title.strip(' ').lower().decode('utf8')).replace(', ', ',')
    for name in os.listdir(target):
        if title in clean(name.lower().decode('utf8')).replace(', ', ','):
            return True
    return False


def remove_m4a(vid_id, target='.'):
    """Checks to see if a song was downloaded.

    TODO: Find a more optimized way of doing this.

    @arg: ytid: Youtube id of song
    @arg: target: Target directory
    """
    for name in os.listdir(target):
        if vid_id in name.decode('utf-8')and name.decode('utf-8').endswith('.m4a'):
            path = os.path.join(target, name)
            try:
                os.remove(path)
            except OSError:
                pass
            return
