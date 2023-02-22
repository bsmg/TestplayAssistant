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
    await interaction.response.defer()
    if interaction.channel.name in testplay_channels:       
        response_message = ""
        
        i = 0
        # Fetch the messages in the channel where the command was sent.        
        async for message in interaction.channel.history(limit=channel_limit, oldest_first=True):
            # Messages in the channel where the command was executed which do not have any reactions and have at least one attachment.
            if (not (message.author.id in excluded_users)) and (len(message.reactions) == 0) and (len(message.attachments) >= 1):
                i += 1
                # Number of testplay.
                response_message += "**" + str(i) + " -**\n"
                # URL of the original message
                response_message += message.jump_url + "\n"
                # Author
                response_message += "**Posted by:** " + message.author.mention
                # Date
                response_message += " *at:* " + message.created_at.strftime("%d-%m-%Y %H:%M") + "\n"
                # Message content
                response_message += "\n"
                response_message += message.content
                response_message += "\n\n"
                # Attachment                
                response_message += "**ATTACHMENT:** " + message.attachments[0].url + "\n"
                response_message += "--------------\n\n"               

        if response_message:
            # Add Response Header and Footer
            response_message = "**Pending testplays**\n\n" + response_message
            response_message += "That should be all of the pending testplays. Have fun testing!"
        else:
            response_message = "No pending testplays found, check back later!"

        await interaction.followup.send(response_message, ephemeral=True)       
    else:
        await interaction.followup.send("You can only use this command on testplay channels!",ephemeral=True)
        print(f'unchecked command on the wrong channel: ' + interaction.channel.name)



token = os.getenv("DISCORD_TOKEN")

bot.run(token)
