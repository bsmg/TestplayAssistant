# TestplayAssistant
A Discord bot to support testplay management for Beat Saber.

## Commands:

- unchecked - Produces a list of messages in the channel that do not have reactions.
- shutdown (admins only) - Shut down the bot.

## Intents and permissions required

![Intents](https://github.com/Undeceiver/TestplayAssistant/blob/main/intents.png)
![Permissions](https://github.com/Undeceiver/TestplayAssistant/blob/main/permissions.png)

## Identifiers in the code

Proper setup also needs to ensure the server identifiers, user identifiers and channel names in the code are adequate.

This is used to identify testplay channels, update slash commands and ignore other bot messages.

Default values are available (they need uncommenting) for BSMG and BSM.

## Discord bot token

The token.txt file should be in the same folder as the bot script, and include only the token used to connect to the bot with Discord.
