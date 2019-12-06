"""
Task 3: You will use Twitter API of streaming to implement the fixed size sampling method (Reservoir Sampling Algorithm) and find popular tags on tweets based on the samples.
"""

'''
Reference to http://docs.tweepy.org/en/v3.4.0/streaming_how_to.html
'''
import sys
import json
from time import time
import math
import random
import tweepy
from tweepy import Stream
from tweepy.streaming import StreamListener

'''
To run code:
spark-submit minh_tran_task3.py
'''

NUMTWEETS = 150
TOPFREQ = 5

'''
Create a class inheriting from StreamListener
# Create a class inheriting from StreamListener,
'''
class tweetsAnalyzer(StreamListener):
    #  passes error messages to an on_error stub, disconnect the stream
    def on_error(self, status):
        print("Error: ", str(status))
        
    # The on_data method of a stream listener receives all messages and calls functions according to the message type
    def on_status(self, status):
        # keep these two variables global to keep track and update
        global numTweets
        global allTweets

        # dictionary to store frequencies of tags
        tagsFreqDict = {}

        # obtain hashtags of that tweet
        currentHashTags = status.entities.get("hashtags")
        # print("hashtags: ", currentHashTags)

        if len(currentHashTags) > 0:
            # update number of tweets with hashtags
            numTweets += 1

            # if number of tweets does not excced max number of tweets
            if numTweets < NUMTWEETS:
                allTweets.append(status)
            else:
                # generate a random tweet index between 0 and n
                randomIdx = random.randint(0, numTweets)

                # With probability s/n, keep the nth element, else discard it
                if randomIdx < NUMTWEETS-1:
                    allTweets[randomIdx] = status

                # after replacement, loop over all tweets
                for tweet in allTweets:
                    hashtags = tweet.entities.get("hashtags")

                    # loop over hashtags
                    for hashtag in hashtags:
                        # hashtags = [{'text':'...', 'indices': [1,3]}]
                        content = hashtag["text"]
                        
                        # update count of hashtags
                        if content not in tagsFreqDict.keys():
                            tagsFreqDict[content] = 1
                        else:
                            tagsFreqDict[content] += 1

                # sort lexicographically based on count and hashtag name
                sortedTweets = sorted(tagsFreqDict.items(), key=lambda x: (-x[1], x[0]))

                if len(sortedTweets) >= TOPFREQ:
                    top5Tweets = sortedTweets[0:TOPFREQ]
                else:
                    top5Tweets = sortedTweets

                # print out prompt
                out = "The number of tweets with tags from the beginning: " + str(numTweets)+"\n"
                for tweet in top5Tweets:
                    out += (tweet[0]+" : "+str(tweet[1])+"\n")

                print(out)



'''
MAIN
'''
if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("Usage: spark-submit minh_tran_task3.py")
        exit(-1)

    # Credentials created for my userid @leotran102
    consumerKey = 'ojWanjYQ4Dce75MNiBRtvJz6J'
    consumerSecretKey = 'KhtfxfFShQI0t9Hv0NC0kGtVedayhTW9Qf9OOk56aarhbHSBUP'
    accessToken = '1019471880808349696-ww4Z6l9EiMQxR4RXywYaZub2pzXFv5'
    accessSecretKey = 'F79tucbWr2nMNChq53vMAxa4x1zaratNf4j8nW4XIbFub'

    # authentication
    authentication = tweepy.OAuthHandler(consumer_key=consumerKey, consumer_secret=consumerSecretKey)
    authentication.set_access_token(key=accessToken, secret=accessSecretKey)
    
    # launch tweetAPI
    tweetAPI = tweepy.API(authentication)
    
    # initiate
    numTweets = 0
    allTweets = []

    # an instance of tweepy.Stream establishes a streaming session and routes messages to StreamListener instance
    # Using that class create a Stream object,
    tweetStream = Stream(auth=authentication, listener=tweetsAnalyzer())

    # Connect to the Twitter API using the Stream.
    # A comma-separated list of phrases which will be used to determine what Tweets will be delivered on the stream.
    tweetStream.filter(track=["trump"])