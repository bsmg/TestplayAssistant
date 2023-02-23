#!/usr/bin/env python3.9

import discord
import os
import json
#from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

server_ids = list(json.loads(os.getenv("SERVER_IDS")))

class TestplayAssistant(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    
    async def setup_hook(self):
        # This copies the global commands over to the guilds.
        for server_id in server_ids:
            server = discord.Object(id=server_id)

            self.tree.copy_global_to(guild=server)
            await self.tree.sync(guild=server)



bot = TestplayAssistant(intents=intents)

testplay_channels = list(json.loads(os.getenv("TESTPLAY_CHANNELS")))
# CMB and MapperBot
excluded_users = list(json.loads(os.getenv("EXCLUDED_USER_IDS")))
channel_limit = int(os.getenv("CHANNEL_LIMIT"))
max_message_length = int(os.getenv("MAX_MESSAGE_LENGTH"))
max_testplays = int(os.getenv("MAX_TESTPLAYS"))

# This command is probably ugly / not handling things properly. I use it mostly to test.
# Empty default permissions means only administrators can run it. You can also just kill the bot :P
@bot.tree.command()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def shutdown(interaction):
    await interaction.response.send_message('Shutting down... Bye!',ephemeral=True)
    print('Received shutdown command. Shutting down.')
    exit()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.tree.command(description="Retrieve a list of pending testplays")
async def listpending(interaction):    
    await interaction.response.defer(ephemeral=True)
    if interaction.channel.name in testplay_channels:
        response_messages = []

        response_message = ""
        
        i = 0
        # Fetch the messages in the channel where the command was sent.        
        async for message in interaction.channel.history(limit=channel_limit, oldest_first=True):
            # Messages in the channel where the command was executed which do not have any reactions and have at least one attachment.
            # Note we check the i on each iteration rather than using a break despite it being less efficient because of the async for, which could produce issues if using break.
            if (i < max_testplays) and (not (message.author.id in excluded_users)) and (len(message.reactions) == 0) and (len(message.attachments) >= 1):
                i += 1
                
                response_header = ""
                response_footer = ""

                # Number of testplay.
                response_header += "**" + str(i) + " -**\n"
                # URL of the original message
                response_header += message.jump_url + "\n"
                # Author
                response_header += "**Posted by:** " + message.author.mention
                # Date
                response_header += " *at:* " + message.created_at.strftime("%d-%m-%Y %H:%M") + "\n\n"

                response_footer += "\n\n"
                # Attachment                
                response_footer += "**FILE:** " + message.attachments[0].url + "\n"
                response_footer += "--------------\n\n"               
                
                # Message content
                # We truncate the content to make sure it doesn't exceed the maximum with the header and footer.
                len_header_footer = len(response_header) + len(response_footer)
                len_content = max(max_message_length - len_header_footer,0)

                response_chunk = ""
                response_chunk += response_header
                if len(message.content) > len_content:
                    response_chunk += message.content[0:len_content]
                else:
                    response_chunk += message.content
                response_chunk += response_footer
                
                # Append to current message if it fits, otherwise create new message
                if (len(response_message) + len(response_chunk)) > max_message_length:
                    response_messages.append(response_message)
                    response_message = ""
                
                # At this point we should be safe that appending these two is guaranteed to be below the limit.
                response_message += response_chunk

        # Last one
        if response_message:
            response_messages.append(response_message)
        
        if len(response_messages) >= 1:
            # Add global response header and footer
            # For simplicity and also to be easier for the user to tell when the bot has finished producing output, we produce these as individual follow-ups
            await interaction.followup.send("**Pending testplays**\n\n", ephemeral=True)

            for response_message in response_messages:
                await interaction.followup.send(response_message, ephemeral=True)

            if i < max_testplays:
                await interaction.followup.send("That should be all of the pending testplays. Have fun testing!", ephemeral=True)
            else:
                await interaction.followup.send("Those are the " + str(i) + " oldest pending testplays. There might be more.", ephemeral=True)
        else:
            await interaction.followup.send("No pending testplays found, check back later!", ephemeral=True)        
    else:
        await interaction.followup.send("You can only use this command on testplay channels!", ephemeral=True)
        print(f'listpending command on the wrong channel: ' + interaction.channel.name)



token = os.getenv("DISCORD_TOKEN")

bot.run(token)
