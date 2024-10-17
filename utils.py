import os
from datetime import datetime

import pytz
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# init slack sdk
slack_token = os.environ.get('SLACK_BOT_TOKEN')
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
def send_msg(action: str, user_id: str, channel_id: str, text: str):
    '''Respond back to Slack on the same channel where the user sent the command'''
    match action:
        case 'clock-in':
            response_text = f'<@{user_id}> has *clocked in* :clock1:'
        case 'clock-out':
            response_text = f'<@{user_id}> has *clocked out* :house:'
        case 'break-15':
            response_text = f'<@{user_id}> went on a *15 minutes break* :coffee:'
        case 'break-30':
            response_text = f'<@{user_id}> went on a *30 minutes break* :coffee:'
        case 'break-60':
            response_text = f'<@{user_id}> went on a *60 minutes break* :knife_fork_plate:'
        case 'break-90':
            response_text = f'<@{user_id}> went on a *90 minutes break* :coffee:'
        case 'back':
            response_text = f'<@{user_id}> is *back from break* :arrow_backward:'
        case _:
            response_text = f'<@{user_id}> used an unknown command: *{action}*'

    # append user note at the end of response_text is user added any
    # underscore to italize
    if text:
        response_text = response_text + f' ~ "_{text}_"'

    try:
        response = client.chat_postMessage(
            text=response_text,
            channel=channel_id,
            blocks=[{
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': response_text
                }
            }]
        )
        return response

    # return exception, because why not?
    except SlackApiError as e:
        return e


#
def send_msg_ephemeral(user: str, channel: str) -> None:
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
