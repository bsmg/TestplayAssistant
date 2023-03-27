# TestplayAssistant
A Discord bot to support testplay management for Beat Saber.

## Commands:

- /listpending - Produces a list of testplays with attachments in the channel that do not have reactions.
- /listpendingdm - Produces a list of testplays with attachments in the channel that do not have reactions.
- /archivetestplays (admins only) - Checks for older testplays and archives them (marks them and DMs the poster). This is run automatically once per day.
- /shutdown (admins only) - Shut down the bot.

## Intents and permissions required

![Intents](https://github.com/Undeceiver/TestplayAssistant/blob/main/intents.png)
![Permissions](https://github.com/Undeceiver/TestplayAssistant/blob/main/permissions.png)

## Environment variables

The bot is configured using environment variables. See example.env for the required variables in a .env file.

## Docker

1. cd into directory and configure a `.env` file
2. Build image `docker build . -t testplayassistant`
3. Run `docker compose up -d` to start the bot
