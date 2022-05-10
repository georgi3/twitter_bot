from config import API_KEY, API_SECRET_KEY, BEARER_TOKEN, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from local_settings import SCREEN_NAME, TARGET_WORDS, TARGET_AUDIENCE, COMMENT_POOL
import tweepy
import time
import datetime
import random
import calendar
import json
import os

# Requests / 3-hour window	300* per user; 300* per app
# https://developer.twitter.com/en/docs/twitter-api/v1/tweets/post-and-engage/api-reference/post-statuses-update
# https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/api-reference/get-tweets-search-stream-rules
# TODO add annotation


def connect():
    """Setting up the api connection"""
    auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)  # Read&Write Permissions
    return tweepy.API(auth)


def connection_verified(api):
    """Verifying twitter api connection"""
    print('Verifying connection..')
    try:
        api.verify_credentials()
        print('Verified')
        return True
    except:
        print('Not Verified...')
        return False


MONTHS_ABR = [calendar.month_abbr[i] for i in range(1, 13)]
MONTHS_ABR[0:0] = '_'


def get_ids(audience, api):
    audience_ids = set()
    for handle in audience:
        print(f'Looking up {handle}')
        user = api.get_user(screen_name=handle)
        audience_ids.add(user.id)
    print(f'{len(audience_ids)} ids have been retrieved.')
    return audience_ids


def get_timeline(user_id, api):
    tweets = api.user_timeline(user_id=user_id, count=20)
    return tweets


def parse_date(date_str):
    month_name = date_str.strip().split()[1]
    month = MONTHS_ABR.index(month_name)
    day = int(date_str.strip().split()[2])
    year = int(date_str[-4:])
    return datetime.date(year=year, month=month, day=day)


def date_check(created_at):
    yesterday = datetime.datetime.today()- datetime.timedelta(days=1)
    return created_at >= yesterday.date()


def word_check(content):
    for word in TARGET_WORDS:
        if word in content:
            return True
    return False


def is_target(tweet):
    """Takes json tweet, returns False if its a garbage tweet, else returns tweet's id"""
    result = tweet.get('id', False)
    created_at = parse_date(tweet.get('created_at', 'Wed March 10 11:29:56 +0000 1900'))
    text = tweet.get('text', '')
    if word_check(text) and date_check(created_at):
        return result
    else:
        return False


def get_targets(api):
    ids = get_ids(TARGET_AUDIENCE, api)
    timelines = [get_timeline(user_id=id_, api=api) for id_ in ids]
    total_n_targets = 0
    targets = []
    for timeline in timelines:
        for tweet in timeline:
            total_n_targets += 1
            target = is_target(tweet._json)
            if target:
                targets.append(target)
            else:
                continue
    print(f'Found {len(targets)}/{total_n_targets} targets.')
    return targets


# TODO add picture
def comment(api, tweet_id):
    reply = random.choice(COMMENT_POOL)
    try:
        api.update_status(status=reply, in_reply_to_status_id=tweet_id, auto_populate_reply_metadata=True)
    except tweepy.TweepyException as err:
        print(f'Tried to comment "{reply}"')
        print(f'Error occurred: {err}')
        return False
    return reply


def ceil(a, b=300):
    return -1 * (-a // b)


def save_dict(dict_):
    if not os.path.isdir('./meta'):
        os.mkdir('./meta')
    with open('./meta/commented_on.json', 'w') as fp:
        json.dump(dict_, fp)
        print('File saved.')


def main(save_json=False):
    api = connect()
    if not connection_verified(api):
        return False
    commented_on = {}
    targets = get_targets(api)
    n_300_tweets = ceil(len(targets))
    seconds = 60 * 60 * 3
    sleep_time = (seconds * n_300_tweets) / len(targets)
    print(f'Commenting {len(targets)} over the span of {(seconds * n_300_tweets)/60/60} hours. Approximated sleep time'
          f' is {sleep_time}')
    i = 0

    for target_id in targets:
        i += 1
        if target_id in commented_on.keys():
            print('Already commented under this tweet, skipping it...')
            continue

        reply = comment(api, target_id)
        if not reply:
            print('Sleeping for 10 min...')
            time.sleep(600)
            continue
        commented_on[target_id] = reply
        print(f'Comment "{reply}" under {target_id}. \nComment {0}/{len(targets)}, sleeping for {sleep_time}...')
        time.sleep(sleep_time)
        if i == 390:
            print(f'Commented {i} times, aborting not to get suspended')
            return commented_on

    if save_json:
        save_dict(commented_on)

    return commented_on


commented_on = main()


