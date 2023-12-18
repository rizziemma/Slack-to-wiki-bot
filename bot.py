import os
from fastapi import FastAPI
from fastapi import Body, FastAPI, Request, Response
from fastapi_slackeventsapi import SlackEventManager

# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import urllib.parse

from scripts import wikify

# WebClient instantiates a client that can call API methods
# When using Bolt, you can use either `app.client` or the `client` passed to listeners.
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
signing_secret = os.environ.get('SLACK_SIGNING_SECRET')

app = FastAPI(docs_url=None,
    title="Bobot",
    description="A bot",
    version="0.1"
)

slack_event_manager = SlackEventManager(singing_secret=signing_secret,
                                       endpoint='/events/',
                                       app=app)

def handle_message(message):
    response = "Sorry, I didn't understand your message :sad-parrot: \n You can ask one of the following commands : \
\n 'hi' \
\n 'wikify <Page Name>' : export the thread to a wiki page \
"
    if message.get("subtype") is None and "hi" in message.get('text'):
        
        return "Hello <@%s>! :party-parrot:" % message["user"]
        
    elif message.get("subtype") is None and "wikify" in message.get('text'):
        page_name = message.get('text').split('wikify ')[1]

        #message not threaded or no page name is given
        if message.get("thread_ts") is None or page_name == [] :
            return message
        thread_ts = message["thread_ts"]
        channel_id = message["channel"]

        try:
            print("fetching replies")
            # conversations.history returns the first 100 messages by default https://api.slack.com/methods/conversations.history$pagination
            conversation_history = client.conversations_replies(channel=channel_id, ts=thread_ts)
            replies = conversation_history["messages"]
            
            print("convert to md")
            message_id = message["client_msg_id"]
            md = wikify.replies_to_md(replies, page_name, message_id, client)

            page_path = "/archives/slack/"+thread_ts
            print("uploading to wiki "+page_path)
            page_url = upload_to_wiki(md, page_name, thread_ts, page_path)

            response = f"Exported thread to page {page_name} at {url}"

        except SlackApiError as e:
            response = "Error creating conversation: {}".format(e)
        except Exception as e:
            response = f"Something went wrong: {e}"

    return response



@slack_event_manager.on("app_mention")
async def app_mention(event_data):
    print(event_data)
    message = event_data["event"]
    channel = message["channel"]
    ts = message["ts"]
    response = handle_message(message)    
    client.chat_postMessage(channel=channel, text=response, thread_ts=ts)
