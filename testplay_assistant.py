#!/usr/bin/env python3.9

import discord
#from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

# Test server
server_id = 1076685386803327006
# BSMG
# server_id = 441805394323439646
# BSM
# server_id = 484909350087950336

server = discord.Object(id=server_id)

class TestplayAssistant(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=server)
        await self.tree.sync(guild=server)



bot = TestplayAssistant(intents=intents)

testplay_channels = ["testplays", "first-map-testing"]
# CMB and MapperBot
excluded_users = [455456822107570186, 701875159673471026]
channel_limit = 1000

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
async def unchecked(interaction):    
    if interaction.channel.name in testplay_channels:       
        response_message = ""

        # Begin the response to the user:
        response_message += "**Unchecked testplays**\n\n"
        
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
                response_message += "**Posted by:** " + message.author.mention + "\n"
                # Date
                response_message += "*at:* " + message.created_at.strftime("%d-%m-%Y %H:%M") + "\n"
                # Message content
                response_message += "\n"
                response_message += message.content
                response_message += "\n\n"
                # Attachment                
                response_message += "**ATTACHMENT:** " + message.attachments[0].url + "\n"
                response_message += "--------------\n\n"               

        response_message += "That should be all the unchecked testplays. Have fun testing!"

        await interaction.response.send_message(response_message, ephemeral=True)       
    else:
        await interaction.response.send_message("You can only use this command on testplay channels!",ephemeral=True)
        print(f'unchecked command on the wrong channel: ' + interaction.channel.name)


token_file = open("token.txt","r")
token = token_file.read()
token_file.close()

bot.run(token)
