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
excluded_users = list(json.loads(os.getenv("EXCLUDED_USER_IDS")))
channel_limit = int(os.getenv("CHANNEL_LIMIT"))
max_message_length = int(os.getenv("MAX_MESSAGE_LENGTH"))
max_testplays = int(os.getenv("MAX_TESTPLAYS"))
checked_reactions = list(json.loads(os.getenv("CHECKED_REACTIONS")))
max_response_embeds = int(os.getenv("MAX_RESPONSE_EMBEDS"))
previewer_prefix = os.getenv("PREVIEWER_PREFIX")

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
    await listpending_withargs(interaction,dm=False)

@bot.tree.command(description="Retrieve a list of pending testplays and send it on DM")
async def listpendingdm(interaction):    
    await interaction.response.send_message("The testplay list will be sent to you over Direct Message.",ephemeral=True)
    await listpending_withargs(interaction,dm=True)

async def listpending_withargs(interaction,dm=False):
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

                    embed.set_author(name=f"{author} ({author.id})")                    
                    
                    preview_url = previewer_prefix + message.attachments[0].url

                    embed.add_field(name="Links", value=f"[Jump to Post]({message.jump_url}) **|** [Download Attachment]({message.attachments[0].url}) **|** [Preview]({preview_url})", inline=True)             
                    embed.add_field(name="User", value=author.mention, inline=True)

                    # Add embed to the list
                    response_messages.append(embed)
        
        if len(response_messages) >= 1:
            # Generate and Send the embed batch
            embed_batch = []
            k = 0
            for j in range(len(response_messages)):
                if k < max_response_embeds:
                    embed_batch.append(response_messages[j])
                    k += 1
                else:
                    await send_response(interaction, dm=dm, mention_instead=False, embeds=embed_batch)
                    embed_batch = []
                    k = 1
                    embed_batch.append(response_messages[j])

            await send_response(interaction, dm=dm, mention_instead=False, embeds = embed_batch)
            #await interaction.followup.send(embeds = embed_batch, ephemeral=True)

            # Add response footer to indicate possible status
            if i < max_testplays:
                await send_response(interaction, dm=dm, mention_instead=False, content="That should be all of the pending testplays. Have fun testing!")                
            else:
                await send_response(interaction, dm=dm, mention_instead=False, content="Those are the " + str(i) + " oldest pending testplays. There might be more.")                
        else:
            # No testplays available
            await send_response(interaction,dm=dm, mention_instead=False, content="No pending testplays found, check back later!")            
    else:
        await send_response(interaction,dm=dm, mention_instead=False, content="You can only use this command on testplay channels!")        
        print(f'listpending command on the wrong channel: ' + interaction.channel.name)

# The mention_instead parameter is used in the case of a failed DM message to send the response on the interaction channel with a mention. If it's False and the DM fails, the message is simply not sent.
async def send_response(interaction, dm=False, mention_instead=False, content = None, **kwargs):
    if dm:
        try:
            await interaction.user.send(content=content,**kwargs)
        except discord.Forbidden:
            if mention_instead:
                if isinstance(content,str):
                    full_content = interaction.user.mention + " (DM could not be sent)\n\n" + content
                    await interaction.channel.send(content=full_content, **kwargs)
                else:
                    full_content = interaction.user.mention + " (DM could not be sent)\n\n"
                    await interaction.channel.send(content=full_content, **kwargs)
            else:
                print(f'Message to user ' + interaction.user.name + ' could not be sent through direct message.')
    else:
        await interaction.followup.send(content=content, ephemeral=True, **kwargs)


token = os.getenv("DISCORD_TOKEN")

bot.run(token)
