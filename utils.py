
import os
from datetime import datetime

import pytz
from slack_sdk import WebClient

# init slack sdk
slack_token = os.environ['SLACK_BOT_TOKEN']
client = WebClient(token=slack_token)
select_block_id: str = 'BfE1N'


#
def convert_timestamp(tmstmp: str) -> str:
    '''Convert Slack's timestamp into human readable PH time in military format'''
    ph_tz = pytz.timezone('Asia/Manila')
    ph_time = datetime.fromtimestamp(float(tmstmp), tz=ph_tz)
    return ph_time.strftime('%Y-%m-%d %H:%M:%S')


#
def build_response(isSuccess: bool, msg: str) -> dict[str, str]:
    '''Build dictionary response'''
    status: str = 'success' if isSuccess else 'failed'
    return {'status': status, 'msg': msg}


#
def send_ephemeral(user: str, channel: str) -> None:
    '''Sends an ephemeral msg to Slack to display available choices to the user'''
    client.chat_postEphemeral(
        text='',
        user=user,
        channel=channel,
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Welcome to Kronos!",
                    "emoji": True
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "plain_text",
                        "text": "Payreto's timestamp logging app, you may reuse the form below as needed.",
                        "emoji": True
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Please select a timestamp action to log..."
                },
                "block_id": select_block_id,
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Action"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": ":clock1: Clock In"
                            },
                            "value": "clock-in"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": ":coffee: Break 15 mins."
                            },
                            "value": "break-15"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": ":coffee: Break 30 mins."
                            },
                            "value": "break-30"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": ":knife_fork_plate: Break 60 mins. / Lunch"
                            },
                            "value": "break-60"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": ":coffee: Break 90 mins."
                            },
                            "value": "break-90"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": ":arrow_backward: Back from break"
                            },
                            "value": "back"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": ":house: Clock Out"
                            },
                            "value": "clock-out"
                        }
                    ],
                    "action_id": "select-action"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Go"
                        },
                        "style": "primary",
                        "value": "go",
                        "action_id": "button-go"
                    }
                ]
            }
        ]
    )
