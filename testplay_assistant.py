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
checked_reactions = list(json.loads(os.getenv("CHECKED_REACTIONS")))


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
        
        i = 0

        # Fetch the messages in the channel where the command was sent.   
        channel_messages = [message async for message in interaction.channel.history(limit=channel_limit)]
        # Iterate oldest first     
        for message in reversed(channel_messages):
            # Messages in the channel where the command was executed which do not have any of the "checked" reactions and have at least one attachment.            
            # Note we check the i on each iteration rather than using a break despite it being less efficient because of the async for, which could produce issues if using break.
            if (i < max_testplays) and (not (message.author.id in excluded_users)) and (len(message.attachments) >= 1):
                # Check the reactions
                reacted = False
                for reaction in message.reactions:
                    if str(reaction) in checked_reactions:
                        reacted = True
                        break

                if not reacted:
                    i += 1
                    
                    author = message.author

                    # Check / Truncate if message is longer than embed description limit
                    user_description = ""
                    if len(message.content) > max_message_length:
                        user_description += message.content[0:max_message_length]
                    else:
                        user_description += message.content

                    embed = discord.Embed(
                        title=f"Post #{i}",
                        color = 0x28b808,
                        timestamp = message.created_at,
                        description=user_description
                    )

                    embed.set_author(name=f"{author} ({author.id})", icon_url=str(author.avatar.url))
                    
                    embed.add_field(name="Links", value=f"[Jump to Post]({message.jump_url}) **|** [Download Attachment]({message.attachments[0].url})", inline=True)             
                    embed.add_field(name="User", value=author.mention, inline=True)

                    # Add embed to the list
                    response_messages.append(embed)

        # Send the embed batch
        for j in range(len(response_messages)):

            await interaction.followup.send(embed = response_messages[j], ephemeral=True)


        
        if len(response_messages) >= 1:
            # Add global response footer
            # For simplicity and also to be easier for the user to tell when the bot has finished producing output, we produce these as individual follow-ups
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
