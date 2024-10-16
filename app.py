import json
import logging
import os

from dotenv import load_dotenv
from flask import Flask, request
from slack_sdk.errors import SlackApiError
from supabase import Client, create_client

from utils import (build_response, convert_timestamp, select_block_id,
                   send_msg, send_msg_ephemeral)

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


# main flask instance
app = Flask(__name__)


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
                slack_response = send_msg(
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
    send_msg_ephemeral(request.form['user_id'], request.form['channel_id'])
    return '', 200
