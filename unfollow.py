from config import API_KEY, API_SECRET_KEY, BEARER_TOKEN, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, EXCEPTIONS, SCREEN_NAME
import tweepy
import time

# https://help.twitter.com/en/using-twitter/twitter-follow-limit


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


def get_followers_ids(handle, api):
    """Returns all the followers"""
    print('Getting followers\' ids')
    followers_iter = tweepy.Cursor(api.get_follower_ids, screen_name=handle).items()
    followers = set()
    i = 0
    while 1:
        try:
            user_id = next(followers_iter)
            followers.add(user_id)
            i +=1
            if i == 330:
                time.sleep(60)
                i = 0
        except tweepy.TweepyException as err:
            print(f'Exception occurred: {err}')
            time.sleep(60*15)
            continue
        except StopIteration:
            print('All the followers are extracted.')
            break
    print(f'Number of followers is {len(followers)}')
    return followers


def get_following(handle, api):
    print("Getting following's ids")
    following_iter = tweepy.Cursor(api.get_friends, screen_name=handle).items()
    while True:
        try:
            user = next(following_iter)
            yield user
        except tweepy.TweepyException as err:
            print(f'Exception occurred: {err}')
            time.sleep(60*15)
            continue
        except StopIteration:
            print('Iterator is exhausted...')
            break


def get_exceptions_ids(exceptions, api):
    """Returns set of followers who might not follow you back, but you still would like to follow them
    :exceptions - people you would like to keep following even they are not following you
    """
    exceptions_ids = set()
    for handle in exceptions:
        user = api.get_user(screen_name=handle)
        exceptions_ids.add(user.id)
    return exceptions_ids


def our_friends(handle, exceptions, api):
    """Extracts and returns users not to unfollow"""
    followers_ids = get_followers_ids(handle, api)
    exceptions_ids = get_exceptions_ids(exceptions, api)
    return followers_ids.union(exceptions_ids)


def is_loser(friends, losers):
    """Checks if retrieved user is in our friend list, if user is not it yields user's id and name."""
    try:
        loser = next(losers)  # iterates over the iterator
        print(loser.id, loser.name)
        if loser.id not in friends:
            print(f'Detected loser to unfollow {loser.name}')
            return loser
        else:
            return False
    except StopIteration:
        print('Looped through users.')
        return False


def unfollow_losers(handle, exceptions, api):
    """Unfollows users who do not follow you back except people who you want to keep following
    -handle: your twitter handle
    -exceptions: users who you want to keep following
    :return the dict of users who were unfollowed
    """
    friends = our_friends(handle, exceptions, api)  # set of user NOT to unfollow
    losers = get_following(handle, api)  # iterator
    unfollow_dict = {}
    i = 0
    while True:
        try:
            loser = is_loser(friends, losers)
            if not loser:
                time.sleep(10)
                continue
            elif i == 390:  # stopper not to get suspended
                print('Unfollowed 390, aborting the program to avoid the suspension...')
                return unfollow_dict
            else:
                loser.unfollow()
                i += 1
                unfollow_dict[loser.id] = loser.name
                print(f'{loser.name} is unfollowed.')
                time.sleep(10)
        except tweepy.TweepyException as err:
            print(f'Exception occurred: {err}')
            print(f'{len(unfollow_dict)} has been unfollowed so far.')
        except StopIteration:
            print('Process finished.')
            print(f'Following list has been cleaned.')
    print(f'{len(unfollow_dict)} has been unfollowed.')
    return unfollow_dict


def main():
    api = connect()
    if not connection_verified(api):
        return False
    unfollowed = unfollow_losers(SCREEN_NAME, EXCEPTIONS, api)
    return unfollowed

# unfollowed = main()
