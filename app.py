import json
import logging
import os
import unittest
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

# app mode
app_mode: str = os.environ.get('APP_MODE')


# init supabase
load_dotenv()
url: str = os.environ.get('SUPABASE_URL')
key: str = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(url, key)

# init slack sdk
slack_token = os.environ['SLACK_BOT_TOKEN']
client = WebClient(token=slack_token)
select_block_id: str = 'BfE1N'


# main flask instance
app = Flask(__name__)


#
def send_msg_to_slack(action: str, user_id: str, channel_id: str, text: str):
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
            text='',
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
def convert_timestamp(tmstmp: str):
    '''Convert Slack's timestamp into human readable PH time in military format'''
    ph_tz = pytz.timezone('Asia/Manila')
    ph_time = datetime.fromtimestamp(float(tmstmp), tz=ph_tz)
    return ph_time.strftime('%Y-%m-%d %H:%M:%S')


#
def build_response(isSuccess: bool, msg: str) -> dict[str, str]:
    '''build dictionary response'''
    status: str = 'success' if isSuccess else 'failed'
    return {
        'status': status,
        'msg': msg
    }


#
@app.route('/interactions', methods=['POST'])
def interactions():
    '''Handler for  interactions based on selected action'''
    payload: dict = json.loads(request.form['payload'])
    action_id = payload['actions'][0]['action_id']

    # only handle if action ID is from button
    if action_id == 'button-go':
        # check if timestamp header exists
        if 'x-slack-request-timestamp' in request.headers:
            slack_timestamp = request.headers['x-slack-request-timestamp']
        else:
            logging.error('Timestamp missing from Slack')
            return build_response(False, 'Timestamp missing from Slack http header'), 400

        # insert to DB
        try:
            (
                supabase.table('Slack Timestamp')
                .insert(
                    {
                        'x-slack-request-timestamp': slack_timestamp,
                        'token': payload['token'],
                        'team_id': payload['team']['id'],
                        'team_domain': payload['team']['domain'],
                        'channel_id': payload['channel']['id'],
                        'channel_name': payload['channel']['name'],
                        'user_id': payload['user']['id'],
                        'user_name': payload['user']['username'],
                        'command': payload['state']['values'][select_block_id]['select-action']['selected_option']['value'],
                        'text': '',
                        'api_app_id': payload['api_app_id'],
                        'is_enterprise_install': payload['is_enterprise_install'],
                        'response_url': payload['response_url'],
                        'trigger_id': payload['trigger_id'],
                        'timestamp': convert_timestamp(slack_timestamp)
                    }
                ).execute()
            )
        except Exception as e:
            logging.exception(e)
            return build_response(False, 'Failed to save timestamp to database! Please contact Client Solutions'), 500

        try:
            # only run slack call on prod
            if app_mode == 'prod':
                slack_response = send_msg_to_slack(
                    action=payload['state']['values'][select_block_id]['select-action']['selected_option']['value'],
                    user_id=payload['user']['id'],
                    channel_id=payload['channel']['id'],
                    text=''
                )
                # looks legit
                logging.exception(slack_response) if isinstance(
                    slack_response, SlackApiError) else logging.info(slack_response)

        except Exception as e:
            logging.exception(e)
            return build_response(False, 'Failed to call Slack API'), 500

        return '', 200

    return '', 200


#
@app.route('/services', methods=['POST'])
def services():
    '''Handler for displaying the app buttons interactions'''
    client.chat_postEphemeral(
        text='',
        user=request.form['user_id'],
        channel=request.form['channel_id'],
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
    return '', 200


#
class UnitTests(unittest.TestCase):
    '''Unit tests for the helper functions'''

    def test_build_response(self):
        '''Tests the "build_response" function'''
        msg: str = 'this is a test string'
        self.assertEqual(
            build_response(True, msg),
            {'status': 'success', 'msg': msg}
        )
        self.assertEqual(
            build_response(False, msg),
            {'status': 'failed', 'msg': msg}
        )

    def test_timestamp_conversion(self):
        '''Tests the "convert_timestamp" function'''
        self.assertEqual(
            convert_timestamp('1727689594'),
            '2024-09-30 17:46:34'
        )
        self.assertEqual(
            convert_timestamp('1727689723'),
            '2024-09-30 17:48:43'
        )


if __name__ == '__main__':
    unittest.main()
