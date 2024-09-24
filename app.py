import logging
import os
from datetime import datetime

import pytz
from dotenv import load_dotenv
from flask import Flask, request
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from supabase import Client, create_client

# init logging
logging.basicConfig(
    format='%(asctime)s-%(levelname)s: %(message)s',
    level=logging.INFO
)


# init supabase
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# init slack sdk
slack_token = os.environ["SLACK_BOT_TOKEN"]
client = WebClient(token=slack_token)

# main flask instance
app = Flask(__name__)


#
def send_msg_to_slack(msg: str, channel_id: str):
    """Responds back to a provided channel"""

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=msg
        )

        logging.info(response)

    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["error"]
        logging.error(e)


# convert epoch time to human time
def convert_timestamp(timestamp: int) -> str:
    """Convert Slack's timestamp into human readable MIL time format"""

    # Create a timezone-aware datetime object for Philippine Time
    philippine_tz = pytz.timezone('Asia/Manila')

    # Convert the timestamp to Philippine Standard Time
    philippine_time = datetime.fromtimestamp(
        timestamp,
        tz=philippine_tz
    )

    return str(philippine_time.strftime('%Y-%m-%d %H:%M:%S'))


# main route to be used by slack
@app.route('/clock-in', methods=['POST'])
def clock_in():
    """Read data sent from Slack then push to db."""

    slack_timestamp = request.headers['x-slack-request-timestamp']
    channel_id = request.form['channel_id']

    try:
        response = (
            supabase.table("Slack Timestamp")
            .insert(
                {
                    "x-slack-request-timestamp": slack_timestamp,
                    "token": request.form['token'],
                    "team_id": request.form['team_id'],
                    "team_domain": request.form['team_domain'],
                    "channel_id": channel_id,
                    "channel_name": request.form['channel_name'],
                    "user_id": request.form['user_id'],
                    "user_name": request.form['user_name'],
                    "command": request.form['command'],
                    "text": request.form['text'],
                    "api_app_id": request.form['api_app_id'],
                    "is_enterprise_install": request.form['is_enterprise_install'],
                    "response_url": request.form['response_url'],
                    "trigger_id": request.form['trigger_id'],
                    "timestamp": convert_timestamp(int(slack_timestamp))
                }
            ).execute()
        )

        logging.info(response)

        send_msg_to_slack(msg="Timestamp saved!", channel_id=channel_id)

        return 'Timestamp saved!'

    except Exception as e:
        logging.exception(e)
        return 'Failed to save timestamp to database! Please contact Client Solutions.'
