#!/usr/bin/env python3.9

import discord
import os
import json
import ast
import datetime
#from discord.ext import commands
from discord import app_commands
from discord.ext import tasks, commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

server_ids = list(json.loads(os.getenv("SERVER_IDS")))
testplay_channels = list(json.loads(os.getenv("TESTPLAY_CHANNELS")))
testplay_channel_ids = ast.literal_eval(os.getenv("TESTPLAY_CHANNEL_IDS"))
excluded_users = list(json.loads(os.getenv("EXCLUDED_USER_IDS")))
channel_limit = int(os.getenv("CHANNEL_LIMIT"))
max_message_length = int(os.getenv("MAX_MESSAGE_LENGTH"))
max_testplays = int(os.getenv("MAX_TESTPLAYS"))
checked_reactions = list(json.loads(os.getenv("CHECKED_REACTIONS")))
max_response_embeds = int(os.getenv("MAX_RESPONSE_EMBEDS"))
previewer_prefix = os.getenv("PREVIEWER_PREFIX")
archive_age_days = int(os.getenv("ARCHIVE_AGE_DAYS"))
archive_task_time = datetime.datetime.strptime(os.getenv("ARCHIVE_TASK_TIME"), '%H:%M').time()
archive_reaction = os.getenv("ARCHIVE_REACTION")

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

        archivetestplays_task.start()

        return

@tasks.loop(time=archive_task_time)
async def archivetestplays_task():
    print(f"Performing automatic old testplay archiving task...")
    n = await archive_old_testplays()
    print(f"Task finished, archived {n} old testplays.")


bot = TestplayAssistant(intents=intents)

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
                await send_response(interaction, dm=dm, mention_instead=False, content=f"Those are the {i} oldest pending testplays. There might be more.")                
        else:
            # No testplays available
            await send_response(interaction,dm=dm, mention_instead=False, content="No pending testplays found, check back later!")            
    else:
        await send_response(interaction,dm=dm, mention_instead=False, content="You can only use this command on testplay channels!")        
        print(f'listpending command on the wrong channel: {interaction.channel.name}')

# The mention_instead parameter is used in the case of a failed DM message to send the response on the interaction channel with a mention. If it's False and the DM fails, the message is simply not sent.
async def send_response(interaction, dm=False, mention_instead=False, content = None, **kwargs):
    if dm:
        await send_dm(interaction.user, interaction.channel, mention_instead, content, **kwargs)
    else:
        await interaction.followup.send(content=content, ephemeral=True, **kwargs)

# This should only be used when sending a DM to a user OUTSIDE OF A COMMAND INTERACTION. Use send_response when the message is in response to a command.
# The mention_instead parameter is used in the case of a failed DM message to send the response on the interaction channel with a mention. If it's False and the DM fails, the message is simply not sent.
async def send_dm(user, mention_channel, mention_instead=False, content = None, **kwargs):
    try:
        await user.send(content=content,**kwargs)
    except discord.Forbidden:
        if mention_instead:
            if isinstance(content,str):
                full_content = f'{user.mention} (DM could not be sent)\n\n{content}'
                await mention_channel.send(content=full_content, **kwargs)
            else:
                full_content = f'{user.mention} (DM could not be sent)\n\n'
                await mention_channel.send(content=full_content, **kwargs)
        else:
            print(f'Message to user {user.name} could not be sent through direct message.')
    
async def archive_old_testplays():
    # Possibly could be some imprecisions with timezones, but the worst that may happen is the testplay stays in the channel a day or two longer until it gets archived. Not a real problem.
    date_threshold = datetime.datetime.today() - datetime.timedelta(days=archive_age_days)

    n = 0

    for tchannel, rchannel in testplay_channel_ids.items():
        tchannel_obj = bot.get_channel(tchannel)
        rchannel_obj = bot.get_channel(rchannel)
        channel_messages = [message async for message in tchannel_obj.history(limit=channel_limit, before=date_threshold)]

        # Iterate oldest first     
        for message in reversed(channel_messages):
            # Messages in the channel which do not have any of the "checked" reactions and have at least one attachment.            
            if (not (message.author.id in excluded_users)) and (len(message.attachments) >= 1):
                # Check the reactions
                reacted = False
                for reaction in message.reactions:
                    if str(reaction) in checked_reactions:
                        reacted = True
                        break

                if not reacted:
                    # We found one.
                    
                    # Add the reaction
                    try:
                        await message.add_reaction(archive_reaction)
                    except discord.Forbidden:
                        print(f"Tried to react to message {message.jump_url} but was forbidden.")

                    # DM the user
                    message_date_str = message.created_at.strftime("%m/%d/%Y %H:%M:%S")
                    warning_message = f"Your testplay ({message.jump_url}) was posted on {message_date_str}. It is now over {archive_age_days} days old and has not been reacted to.\n\n"
                    warning_message += f"I have now marked it with {archive_reaction}.\n\n"
                    warning_message += f"If you still require a testplay for this map, please re-post your testplay message."

                    await send_dm(message.author, rchannel_obj, mention_instead=True, content=warning_message)

                    n+=1

    return n

@bot.tree.command(description="Archive all old testplays in ALL testplay channels")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def archivetestplays(interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(f"Archiving all old testplays in all testplay channels...", ephemeral=True)
    n = await archive_old_testplays()
    await interaction.followup.send(f"Found {n} old testplays that were archived.",ephemeral=True)


token = os.getenv("DISCORD_TOKEN")

bot.run(token)
