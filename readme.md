# Kronos

A smol microservice for Slack that works as an employee timestamp recorder. Uses Supabase to store the time logs.

## Setup

1. Create a Supabase table with the following columns:

- x-slack-request-timestamp
- token
- team_id
- team_domain
- channel_id
- channel_name
- user_id
- user_name
- command
- text
- api_app_id
- is_enterprise_install
- response_url
- trigger_id
- timestamp

2. Register a Slack App with Channel Write permissions.
3. Add the Slash commands with the URL params seen on line 50; e.g. "https://yourdomain.com/time/clock-in".
4. Add the App as an integration on the channel where you want the users to call it from.
