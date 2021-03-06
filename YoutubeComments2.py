#!/usr/bin/python

# Usage example:
# python comment_threads.py --channelid='<channel_id>' --videoid='<video_id>' --text='<text>'

import httplib2
import os
import sys
import csv

from apiclient.discovery import build_from_document
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains

# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
YOUTUBE_READ_WRITE_SSL_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0
To make this sample run you will need to populate the client_secrets.json file
found at:
   %s
with information from the APIs Console
https://console.developers.google.com
For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# Authorize the request and store authorization credentials.
def get_authenticated_service(args):
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_READ_WRITE_SSL_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, args)

  # Trusted testers can download this discovery document from the developers page
  # and it should be in the same directory with the code.
  with open("youtube-v3-discoverydocument.json", "r") as f:
    doc = f.read()
    return build_from_document(doc, http=credentials.authorize(httplib2.Http()))


# Call the API's commentThreads.list method to list the existing comments.

def get_comment_threads(youtube, video_id, comments):
   threads = []
   results = youtube.commentThreads().list(
     part="snippet",
     videoId=video_id,
     textFormat="plainText",
   ).execute()

  #Get the first set of comments
   for item in results["items"]:
    threads.append(item)
    comment = item["snippet"]["topLevelComment"]
    text = comment["snippet"]["textDisplay"]
    comments.append(text)

  #Keep getting comments from the following pages
   while ("nextPageToken" in results):
    results = youtube.commentThreads().list(
      part="snippet",
      videoId=video_id,
      pageToken=results["nextPageToken"],
      textFormat="plainText",
    ).execute()
    for item in results["items"]:
      threads.append(item)
      comment = item["snippet"]["topLevelComment"]
      text = comment["snippet"]["textDisplay"]
      comments.append(text)

   print "Total threads: %d" % len(threads)

   return threads

def get_comments(youtube, parent_id, comments):
  results = youtube.comments().list(
    part="snippet",
    parentId=parent_id,
    textFormat="plainText"
  ).execute()

  for item in results["items"]:
    text = item["snippet"]["textDisplay"]
    comments.append(text)

  return results["items"]
  

if __name__ == "__main__":

  argparser.add_argument("--videoid", help="Required; ID for video for which the comment will be inserted.")
  args = argparser.parse_args()
  youtube = get_authenticated_service(args)
  links = [] 
  with open(args.videoid, 'rb') as csvfile:
     spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
     for row in spamreader:
         newstring = str(row)
         newstring = newstring.replace("['","")
         newstring = newstring.replace("']","")
         links.append(newstring)

  for i in links:  
      try:  
        comments = []
        print "link", i
        vidid = i
        video_comment_threads = get_comment_threads(youtube, vidid, comments)
        x = 0
        for thread in video_comment_threads:
            get_comments(youtube, thread["id"], comments)
        print "Total comments: %d" % len(comments)
    
      except HttpError, e:
        print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
    
      output_file = open("%s.txt" % (i), 'w+') 
      for comment in comments:
        try:
            output_file.write(comment.encode("utf-8") + "\n")
        except:
            print(comment)
      output_file.close()


