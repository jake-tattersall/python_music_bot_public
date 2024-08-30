import os
from datetime import datetime, timedelta

import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import tasks

from methods import reset
from vars import (TOKEN, bot, loopQueue, loopSong,
                  server_indep_vars, songs, voice)

# Specify how long the bot should run for the day
end_time = datetime.now() + timedelta(hours=20)

@bot.event
async def on_ready():
    '''Prints to console and changes activity to something random'''

    # Initialize values
    for guild in bot.guilds:
        guild = guild.id
        voice.update({guild:None})
        loopSong.update({guild:None})
        loopQueue.update({guild:None})
        songs.update({guild:list()})
        reset(guild)

    randomWordURL = "https://randomword.com/"
    word = "random_word"
    wordDef = "random_word_definition"

    try:
        # Send a GET request to the webpage
        response = requests.get(randomWordURL)
        response.raise_for_status()  # Raise an HTTPError for bad requests

        # Parse the HTML content of the webpage
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the first <li> element with the specified class
        dailyWord = soup.find(id=word)
        dailyDefinition = soup.find(id=wordDef)

        if dailyWord and dailyDefinition:
            # Get the text content of the element
            dailyWord = dailyWord.text.strip()
            dailyDefinition = dailyDefinition.text.strip()

            # Change status to that word
            await bot.change_presence(status = discord.Status.online, activity=discord.Activity(type=discord.ActivityType.playing, name = f'"{dailyWord}"'))
            server_indep_vars['word'] = dailyWord
            server_indep_vars['definition'] = dailyDefinition
        else:
            print(f"No element found with id '{word}' OR No element found with id '{wordDef}'.")

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        await bot.change_presence(status = discord.Status.online, activity=discord.Activity(type=discord.ActivityType.playing, name = "No random word"))
    
    print(f"\nThe bot {bot.user} is ready!\n")
    shutdown.start()
    


@bot.event
async def on_voice_state_update(member, before, after):
    '''Performs actions when someone enters/leaves a VC or changes their voice state'''
    
    guild = member.guild.id

    # Deafens the bot when joining a call
    if member.id == 891328590698926170 and before.channel == None and after.channel != None:
        await member.guild.change_voice_state(channel=after.channel, self_deaf=True)
    
    # Fixes the bot when being manually disconnected from a channel
    if member.id == 891328590698926170 and after.channel== None:
        try:
            await voice[guild].disconnect()
            voice[guild].cleanup()
        except:
            print("@bot.event on_voice_state_update - No need to disconnect or cleanup")
        voice[guild] = None
        reset(guild)

    # Bot leaves when channel is empty
    if voice[guild] != None:
        if voice[guild].channel == before.channel:
            people = []
            for member in before.channel.members:
                if not member.bot:
                    people.append(member)
                    break

            if len(people) == 0:
                await voice[guild].disconnect()
                voice[guild].cleanup()
                print("disconnected automatically!")


@bot.event
async def on_application_command_error(ctx, error):
    await ctx.respond(f"Error! {error}")


@tasks.loop(minutes=1)
async def shutdown():
    '''Shuts the bot down after a specific time has been reached'''
    if datetime.now() > end_time:
        await bot.change_presence(status = discord.Status.offline)
        await bot.close()


@shutdown.error
async def shutdown_error(error):
    print("error!")


try:
    # Adds COGs to the command lists
    for filename in os.listdir('commands'):
        if filename.endswith('.py'):
            print(filename)
            bot.load_extension(f'commands.{filename[:-3]}') 
    bot.run(TOKEN)
except Exception as e:
    print(e)
    print("Bot shutdown")
finally:
    print("Exiting")
    exit(1)


