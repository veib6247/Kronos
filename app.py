import json
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

# main flask instance
app = Flask(__name__)

# expected form item passed by Slack via slash commands
slack_form_items = [
    'token',
    'team_id',
    'team_domain',
    'channel_id',
    'channel_name',
    'user_id',
    'user_name',
    'command',
    'text',  # can be empty
    'api_app_id',
    'is_enterprise_install',
    'response_url',
    'trigger_id'
]

# list of valid url param actions
actions = [
    'clock-in',
    'clock-out',
    'break-15',
    'break-30',
    'break-60',
    'break-90',
    'back'
]


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
            response_text = f'<@{user_id}> went on a *60 minutes break* :coffee:'
        case 'break-90':
            response_text = f'<@{user_id}> went on a *90 minutes break* :coffee:'
        case 'back':
            response_text = f'<@{user_id}> is *back from break*'
        case _:
            response_text = f'<@{user_id}> used an unknown command: *{action}*'

    # append user note at the end of response_text is user added any
    # underscore to italize
    if text:
        response_text = response_text + f' ~ "_{text}_"'

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            blocks=[
                {
                    'type': 'section',
                    'text': {
                            'type': 'mrkdwn',
                            'text': response_text
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Schedule"
                            },
                            "value": "view_schedule",
                            "action_id": "button_click_schedule"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Check Tasks"
                            },
                            "value": "check_tasks",
                            "action_id": "button_click_tasks"
                        }
                    ]
                }
            ]

        )
        return response
    except SlackApiError as e:
        return e


#
def convert_timestamp(timestamp: str):
    '''Convert Slack's timestamp into human readable PH time in MIL format'''

    philippine_tz = pytz.timezone('Asia/Manila')
    philippine_time = datetime.fromtimestamp(
        int(timestamp),
        tz=philippine_tz
    )
    return str(philippine_time.strftime('%Y-%m-%d %H:%M:%S'))


# main route to be used by slack
@app.route('/time/<action>', methods=['POST'])
def time(action: str):
    '''Read data sent from Slack then push to db'''

    if action not in actions:
        return {
            'status': 'failed',
            'msg': f"invalid command: '{action}'"
        }, 400

    # check if timestamp header exists
    if 'x-slack-request-timestamp' in request.headers:
        slack_timestamp = request.headers['x-slack-request-timestamp']
    else:
        logging.error('Timestamp missing from Slack')
        return {
            'status': 'failed',
            'msg': 'Timestamp missing from Slack http header'
        }, 400

    # return 400 if any of the form items are missing from Slack's payload
    for item in slack_form_items:
        if item not in request.form:
            err_msg = f'{item} missing from Slack http body'
            logging.error(err_msg)
            return {
                'status': 'failed',
                'msg': err_msg
            }, 400

    # try parse timestamp
    # this will probably never throw but just in case Slack messes up
    try:
        int(slack_timestamp)
    except ValueError as e:
        logging.error(e)
        return {
            'status': 'failed',
            'msg': 'Unable to parse timestamp from Slack, invalid value'
        }, 400

    try:
        (
            supabase.table('Slack Timestamp')
            .insert(
                {
                    'x-slack-request-timestamp': slack_timestamp,
                    'token': request.form['token'],
                    'team_id': request.form['team_id'],
                    'team_domain': request.form['team_domain'],
                    'channel_id': request.form['channel_id'],
                    'channel_name': request.form['channel_name'],
                    'user_id': request.form['user_id'],
                    'user_name': request.form['user_name'],
                    'command': request.form['command'],
                    'text': request.form['text'],
                    'api_app_id': request.form['api_app_id'],
                    'is_enterprise_install': request.form['is_enterprise_install'],
                    'response_url': request.form['response_url'],
                    'trigger_id': request.form['trigger_id'],
                    'timestamp': convert_timestamp(slack_timestamp)
                }
            ).execute()
        )

        # Ensure that the app is added in the Slack channel's integration tab for it to work!
        # only run slack call on prod
        if app_mode == 'prod':
            slack_response = send_msg_to_slack(
                action=action,
                user_id=request.form['user_id'],
                channel_id=request.form['channel_id'],
                text=request.form['text']
            )
            logging.info(slack_response)

        return '', 200

    except Exception as e:
        logging.exception(e)
        return {
            'status': 'failed',
            'msg': 'Failed to save timestamp to database! Please contact Client Solutions'
        }, 500


# handler for app buttons interactions
@app.route('/interactions', methods=['POST'])
def interactions():
    payload: dict = json.loads(request.form['payload'])
    action_id = payload['actions']['action_id']

    return f'Action ID: {action_id}', 200
