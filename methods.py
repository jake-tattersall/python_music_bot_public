import asyncio
import random
from datetime import timedelta

import discord
import yt_dlp as ytdl

from vars import (FFMPEG_OPTIONS, Song, bot, loopQueue, loopSong, songs, voice,
                  ydl_opts)


def reset(id):
    '''Resets the data for the passed guild id's info'''
    songs[id].clear()
    loopQueue[id] = False
    loopSong[id] = False


def checkCtx(ctx) -> bool:
    '''Returns True if the user is in a valid voice channel. Returns False if not'''
    try:
        if ctx.user.voice.channel == None:
            return False
    except:
        return False

    return True


def checkArg(arg) -> bool:
    '''Returns True if the user entered a valid search or link. Returns False if not'''
    if arg == None:
        return False
    elif arg.replace("'","").replace('"',"").strip() == "":
            return False

    return True



async def getSong(arg, ctx) -> Song:
    '''
    Returns a loaded Song object.
    
    Raises errors listed in fillSongData
    '''
    song = Song()

    await song.fillSongData(arg, ctx)
    song.addedby = ctx.user.name

    return song


async def getSongs(arg, ctx) -> list:

    songs = list()

    try:
        ydl = ytdl.YoutubeDL(ydl_opts)
        ytsearch = False

        await ctx.followup.send("Please wait...")
        #msg = await ctx.send("0 songs loaded...")

        try:
            info = ydl.extract_info(arg, download=False)
        except ytdl.utils.DownloadError:
            ytsearch = True
            info = ydl.extract_info(f"ytsearch:{arg}", download=False)

        ydl.close()

        # If playlist
        if info.get('playlist_count') and info.get('playlist_count') != 1:
            for entry in info.get('entries'):
                song = Song()

                await song.fillSongData(entry.get("id"), entry, ytsearch)
                song.addedby = ctx.user.name

                songs.append(song)

        # If song
        else:
            song = Song()

            await song.fillSongData(arg, info, ytsearch)
            song.addedby = ctx.user.name

            songs.append(song)

    except Exception as e:
        raise e
    finally:
        return songs





async def firstPlay(ctx, song) -> None:
    '''
    To use when playing a song for the first time and/or to override the queue
    '''
    guild = ctx.guild.id
    channel = ctx.user.voice.channel

    # Clear guild info, then connect to VC
    reset(guild)
    voice[guild] = await voiceConnect(voice[guild], channel)

    try:
        voice[guild].stop()
    except:
        pass

    # Begin playing song
    voice[guild].play(discord.FFmpegOpusAudio(song.getURL(), **FFMPEG_OPTIONS))


async def ss(ctx):
    '''Performs shuffle of queue including currentSong, turns LoopQueue to True, and begins playing the new song'''
    guild = ctx.guild.id

    length = len(songs[guild])
    if length < 2:
        await ctx.respond("Not enough in queue to super shuffle", ephemeral=True)
        return


    def find_indices(list, term):
        '''Returns a list of the indices of the term found inside a list'''
        return [index for (index, item) in enumerate(list) if item.url == term]


    def pop_at(index):
        '''Removes all components of a song at a given index'''
        songs[guild].pop(index)


    try:
        if length >= 2:
            # Shuffle and then unpack the new ordered lists
            random.shuffle(songs[guild])
            voice[guild] = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            loopSong[guild] = False
            loopQueue[guild] = True

            for song in songs[guild]:
                indices = find_indices(songs[guild], song.url)
                if len(indices) > 1:
                    indices.reverse()
                    for x in range(0, len(indices)-1):
                        pop_at(indices[x])

            try:
                voice[guild].stop()
            except:
                pass

            await ctx.respond("Super Shuffled!")

        elif len(songs[guild]) == 1:
            await ctx.respond("Not enough songs in queue", ephemeral=True)
        else:
            await ctx.respond("Nothing in queue to shuffle", ephemeral=True)
    except Exception as e:
        print(e)



async def playNext(ctx: discord.commands.context.ApplicationContext):
    '''Begins playing the next song in queue. Tests for queue'''
    guild = ctx.guild.id
    

    while voice[guild] and len(songs[guild]) != 0: # Repeat while connected and songs to play
        while voice[guild] != None and voice[guild].is_playing():       # Ensures audio is done before proceeding
            await asyncio.sleep(1)

        try:
            if len(songs[guild]) == 1:      # If queue is empty
                if loopSong[guild] == True:        # If song is to loop, play the looped song
                    URL = songs[guild][0].getURL()
                    voice[guild].play(discord.FFmpegOpusAudio(URL, **FFMPEG_OPTIONS))

                else: # Ends process if queue empty and loop is not on
                    reset(guild)   

            else:       # If there is queue
                if loopSong[guild] == False and loopQueue[guild] == False:        # If no loop or queue loop, play next
                    songs[guild].pop(0)

                elif loopQueue[guild] == True:     # If loop queue is on, play next song and re-add current song to queue
                    songs[guild].append(songs[guild].pop(0))

                # Play next song
                URL = songs[guild][0].getURL()
                voice[guild].play(discord.FFmpegOpusAudio(URL, **FFMPEG_OPTIONS))


        except IndexError as e: # To take place if bot leaves and playNext attempts to move to next song
            pass 
        except discord.errors.ClientException as e:
            print(f"discord.errors.ClientException : {e}")
        except AttributeError as e:
            print(f"AttributeError : {e}")
        except discord.ext.commands.errors.CommandInvokeError as e:
            print(f"discord.ext.commands.errors.CommandInvokeError : {e}")
        except TypeError as e:
            print(f"TypeError : {e}")
        except Exception as e:
            print(f"Error type {type(e)} from something in playNext : {e}")


    try:
        endTime = timedelta(0)
        while not voice[guild].is_playing():
            endTime += timedelta(seconds=1)
            if endTime > timedelta(seconds=1800): # Bot auto disconnects after 30 minutes of not playing anything
                await voice[guild].disconnect()
                break
            await asyncio.sleep(1)
            if voice[guild] == None:
                break
    except:
        pass


async def voiceConnect(voice: discord.voice_client.VoiceClient, channel: discord.channel.VoiceChannel):
    '''Joins the VC'''
    if voice and voice.is_connected():
        pass
    else:
        try:
            await voice.disconnect()
            voice.cleanup()
            voice = await channel.connect(reconnect=True)
        except:
            voice = await channel.connect(reconnect=True)
        finally:
            await voice.guild.change_voice_state(channel=channel, self_deaf=True)

    return voice


async def destroyPlayNexts(guild):
    '''Destroys duplicate and unnecessary playNexts to keep from taking up resources'''
    for task in asyncio.all_tasks():
        if task.get_name() == f"playNext{guild}":
            task.cancel()


async def createPlayNexts(ctx):
    '''Creates a playNext task'''
    guild = ctx.guild.id

    await destroyPlayNexts(guild)

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(coro_or_future=asyncio.create_task(coro=playNext(ctx), name=f"playNext{guild}"), loop=loop)