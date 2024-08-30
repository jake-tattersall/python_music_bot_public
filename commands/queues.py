import asyncio
import random
from datetime import timedelta

import discord
from discord.ext import commands
from discord.utils import get

from methods import ss
from vars import color, helps, loopQueue, loopSong, songs, voice, lock


class queues(commands.Cog, name="queues"):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description = helps['queues']['Remove'])
    async def remove(
        self,
        ctx, 
        *, arg : discord.Option(name="position", description="Number in the queue", required=True) # type: ignore
        ):
        '''Removes specified item from the queue'''

        guild = ctx.guild.id

        if arg == None:
            await ctx.respond("Please make sure to input a valid number.", ephemeral=True)
            return
        elif arg.replace("'","").replace('"',"").strip() == "":
                await ctx.respond("Please make sure to input a valid number.", ephemeral=True)
                return
        arg = arg.replace("'","").replace('"',"").strip()

        try:
            arg = int(arg)
        except:
            await ctx.respond("Please enter a number currently in the queue.", ephemeral=True)
            return

        await ctx.defer()

        try:
            await lock.acquire()

            await ctx.respond("Looking...")
            
            try:
                songRemoved = songs[guild].pop(arg)
                removeEmbed = discord.Embed(color=color)
                removeEmbed.add_field(name="Song Removed", value= str(arg) + ": [**" + songRemoved.title + "**](" + songRemoved.url + ")")
                await ctx.send(embed=removeEmbed)
            except:
                await ctx.respond("No song in queue with that number", ephemeral=True)
        except Exception as e:
            print(e)
            print(type(e))
            await ctx.followup.send("Some error occurred...")
        finally:
            try:
                lock.release()
            except RuntimeError: # If lock was already released
                pass
        
        # ----------------------------------------
        # End of Remove
        # ----------------------------------------


    @commands.slash_command(description = helps['queues']['Skip'], aliases = ["s"])
    async def skip(
        self, 
        ctx,
        *, position : discord.Option(name='position', description='(optional) The position to skip to. Defaults to 1, the next song', default="1") # type: ignore
        ):
        '''Skips the current song or moves to requested position. Calls PlayNext to test for queue'''

        guild = ctx.guild.id

        # Check if voice connected
        if voice[guild] == None:
            await ctx.respond("I am not in a voice channel", ephemeral=True)
            return

        # Check if position is valid, numerically speaking
        try:
            position = int(position)
        except:
            await ctx.send(f"Please use a valid position number next time. {position} is invalid.")
            position = 1

        # Check if position is valid, logically speaking
        if (position >= len(songs[guild]) and len(songs[guild]) > 1) or position <= 0: 
            await ctx.respond(f"Please use a valid position number. There are {len(songs[guild])-1} items in queue", ephemeral=True)
            return
        
        await ctx.defer()

        # Perform skipping
        try:
            await lock.acquire()
            cs = songs[guild][0]
            if loopSong[guild] == True:
                voice[guild].stop()
                skipEmbed = discord.Embed(title="Restarted! LoopSong is On!", color=color)
                if cs.duration_int == 0:
                    skipEmbed.add_field(name="Song Skipped:", value= "**[" + cs.title + "](" + cs.url + ")** | `Livestream`")
                else:
                    skipEmbed.add_field(name="Song Skipped:", value= "**[" + cs.title + "](" + cs.url + ")** | `Duration: " + cs.duration_dt + "`")
                skipEmbed.set_thumbnail(url=cs.thumbnail)
                if loopQueue[guild]:
                    skipEmbed.set_footer(text="LoopSong: ✅ | LoopQueue: ✅")
                else:
                    skipEmbed.set_footer(text="LoopSong: ✅ | LoopQueue: ❌")
                await ctx.respond(f'"{cs.title}" restarted. You have LoopSong on.', embed=skipEmbed)
                return
            elif len(songs[guild]) == 1:
                voice[guild].stop()
                await ctx.respond(f"Skipped! And there are no more songs to play!")
                return
            elif len(songs[guild]) == 0:
                voice[guild].stop()
                await ctx.respond("Nothing to Skip!", ephemeral=True)
                return
            else:
                try:
                    
                    if loopQueue[guild]:
                        for i in range(1, position):
                            songs[guild].append(songs[guild].pop(0))
                    else:
                        for i in range(1, position):
                            songs[guild].pop(0)

                    newcs = songs[guild][1] # Final skip handled in playNext, so keep this next in line
                    skipEmbed = discord.Embed(title="Skipped!", color=color)
                    if cs.duration_int == 0:
                        skipEmbed.add_field(name="Song Skipped:", value= "**[" + cs.title + "](" + cs.url + ")** | `Livestream`")
                    else:
                        skipEmbed.add_field(name="Song Skipped:", value= "**[" + cs.title + "](" + cs.url + ")** | `Duration: " + cs.duration_dt + "`")
                    if newcs.duration_int == 0:
                        skipEmbed.add_field(name="Now Playing:", value="**[" + newcs.title + "](" + newcs.url + ")** | `Livestream`", inline=False)
                    else:
                        skipEmbed.add_field(name="Now Playing:", value="**[" + newcs.title + "](" + newcs.url + ")** | `Duration: " + newcs.duration_dt + "`", inline=False)
                    skipEmbed.set_thumbnail(url=newcs.thumbnail)

                    if loopSong[guild] == False and loopQueue[guild] == False:
                        skipEmbed.set_footer(text="LoopSong: ❌ | LoopQueue: ❌")
                        voice[guild].stop()
                        await ctx.respond("Skipped!", embed=skipEmbed)
                    elif loopQueue[guild] == True:
                        skipEmbed.set_footer(text="LoopSong: ❌ | LoopQueue: ✅")
                        voice[guild].stop()
                        await ctx.respond("Skipped! But still in Queue!", embed=skipEmbed)
                    else:
                        voice[guild].stop()
                        
                except discord.errors.ClientException as e:
                    print(e)
                except discord.ext.commands.errors.CommandInvokeError as e:
                    print(e)
                except TypeError as e:
                    print(e)
                except KeyError as e:
                    print(e)
                except AttributeError as e:
                    print(e)
                except Exception as e: 
                    print("Error from something in Skip")
                    print(e)
        except Exception as e:
            print(e)
            print(type(e))
            await ctx.followup.send("Some error occurred...")
        finally:
            try:
                lock.release()
            except RuntimeError: # If lock was already released
                pass

        # ----------------------------------------
        # End of Skip
        # ----------------------------------------



    @commands.slash_command(description = helps['queues']['Queue'], aliases = ["q"])
    async def queue(
        self, 
        ctx, 
        *, page : discord.Option(name="page", description="(optional) Page to view. Defaults to 1", default="1") # type: ignore
        ):
        '''Sends embed listing queue order. Cannot fit more than 1024 chars in one field so split up'''
        guild = ctx.guild.id
        doWait = True
        fields = {}


        def checkPageFirst(react, user):
            return react.message.id == msg1.id and str(react.emoji) in ["▶️", "⏩"] and user.bot == False
        def checkPageAny(react, user):
            return react.message.id == msg1.id and str(react.emoji) in ["⏪", "◀️", "▶️", "⏩"] and user.bot == False
        def checkPageLast(react, user):
            return react.message.id == msg1.id and str(react.emoji) in ["⏪", "◀️"] and user.bot == False

        async def getFields():
            count = 0
            count2 = 1
            totalLen = 0
            fields = {}
            fields[count2] = []

            # Check if songs left in queue
            queueLength = len(songs[guild]) - 1
            if queueLength < 0:
                await ctx.send("Nothing left in the queue! Music has been stopped or ended!")
                return


            while count != queueLength and totalLen < 6000:
                count += 1
                song = songs[guild][count]
                if count == 1:
                    name = "___Up Next:___"
                else:
                    name = "\u200b"
                if song.duration_int == 0:
                    indSong = "`" + str(count) + "`: [" + song.title + "](" + song.url + ") | `Duration: Livestream | Added by " + song.addedby + "`"
                    field = discord.EmbedField(name=name, value=indSong, inline=False)
                else:
                    indSong = "`" + str(count) + "`: [" + song.title + "](" + song.url + ") | `Duration: " + song.duration_dt + " | Added by " + song.addedby + "`"
                    field = discord.EmbedField(name=name, value=indSong, inline=False)
                totalLen += len(indSong) + len(name)
                
                fields[count2].append(field)

                if len(fields[count2]) == 11 or totalLen > 6000:
                    queueEmbed.remove_field(-1)
                    oldField = fields[count2].pop()
                    count2 += 1
                    fields[count2] = []
                    fields[count2].append(oldField)
                    totalLen = 0

            return fields, count2
        
        
        async def footer():
            totalDur = timedelta(days=0)
            for s in songs[guild]:
                totalDur = totalDur + timedelta(seconds=s.duration_int)
            totalDur = str(totalDur)

            tqt = "Page " + str(page) + "/" + str(len(fields)) + " | Total Queue Time: " + totalDur

            if loopSong[guild] and loopQueue[guild]:
                queueEmbed.set_footer(text=tqt + " | LoopSong: ✅ | LoopQueue: ✅")
            elif loopSong[guild] and not loopQueue[guild]:
                queueEmbed.set_footer(text=tqt + " | LoopSong: ✅ | LoopQueue: ❌")
            elif not loopSong[guild] and loopQueue[guild]:
                queueEmbed.set_footer(text=tqt + " | LoopSong: ❌ | LoopQueue: ✅")
            else:
                queueEmbed.set_footer(text=tqt + " | LoopSong: ❌ | LoopQueue: ❌")


        
        # Check if songs left in queue
        queueLength = len(songs[guild]) - 1
        if queueLength < 0:
            await ctx.respond("Nothing left in the queue! Music has been stopped or ended!", ephemeral=True)
            return

        try:
            page = int(page)
        except:
            await ctx.send("Please use a valid page number next time.")
            page = 1

        await ctx.defer()

        try:
            await lock.acquire()

            channel = voice[guild].channel
            queueEmbed = discord.Embed(title="Queue for " + ctx.guild.name + " - " + channel.name, color=color)

            fields, count2 = await getFields()
            cs = songs[guild][0]
            if page == 1:
                if cs.duration_int == 0:
                    queueEmbed.add_field(name = "___Now Playing in " + str(channel) + ":___", value = "**[" + cs.title + "](" + \
                        cs.url + ")** | `Duration: Livestream | Added by " + cs.addedby + "`")
                else:
                    queueEmbed.add_field(name = "___Now Playing in " + str(channel) + ":___", value = "**[" + cs.title + "](" + \
                        cs.url + ")** | `Duration: " + cs.duration_dt + " | Added by " + cs.addedby + "`")
            try:
                for field in fields[page]:
                    queueEmbed.append_field(field)
            except:
                await ctx.respond(f"Please use a valid page number. There are {len(fields)} pages")
                return

            if len(songs[guild]) == 1:
                queueEmbed.set_thumbnail(url=cs.thumbnail)
                if loopSong[guild] == True:
                    queueEmbed.add_field(name = "LoopSong", value = "✅")
                else:
                    queueEmbed.add_field(name = "LoopSong", value = "❌")
                await ctx.followup.send(embed=queueEmbed)
            else:
                
                await footer()
                
                msg1 = await ctx.followup.send(embed=queueEmbed)
                if count2 > 1:
                    msg2 = await ctx.send(f"⚠️ `{queueLength-len(fields[1])}` songs are not listed! The queue is too long to show them all! ⚠️ (Press the arrow to move pages. Timeout to see more is 60 seconds from each arrow)")
                    while doWait and count2 > 1:
                        try:
                            if page == 1:
                                await msg1.add_reaction("▶️")
                                await msg1.add_reaction("⏩")
                                react, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=checkPageFirst)
                            elif page == list(fields.keys())[-1]:
                                await msg1.add_reaction("⏪")
                                await msg1.add_reaction("◀️")
                                react, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=checkPageLast)
                            else:
                                await msg1.add_reaction("⏪")
                                await msg1.add_reaction("◀️")
                                await msg1.add_reaction("▶️")
                                await msg1.add_reaction("⏩")
                                react, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=checkPageAny)
                        except asyncio.TimeoutError:
                            await msg2.edit("Got rid of the embed for space. Recall queue command to see the queue again.")
                            await msg1.delete()
                            doWait = False
                            return
                        except:
                            await msg2.edit("Got rid of the embed for space. Recall queue command to see the queue again.")
                            await msg1.delete()
                            doWait = False
                            return
                        else:
                            if react.emoji == "▶️":
                                page += 1
                            elif react.emoji == "⏩":
                                page = len(fields)
                            elif react.emoji == "⏪":
                                page = 1
                            else:
                                page -= 1
                            try:
                                queueEmbed.clear_fields()
                                fields, count2 = await getFields()
                                if page == 1:
                                    if cs.duration_int == 0:
                                        queueEmbed.add_field(name = "___Now Playing in " + str(channel) + ":___", value = "**[" + cs.title + "](" + \
                                            cs.url + ")** | `Duration: Livestream | Added by " + cs.addedby + "`")
                                    else:
                                        queueEmbed.add_field(name = "___Now Playing in " + str(channel) + ":___", value = "**[" + cs.title + "](" + \
                                            cs.url + ")** | `Duration: " + cs.duration_dt + " | Added by " + cs.addedby + "`")
                                for field in fields[page]:
                                    queueEmbed.append_field(field)
                                await footer()
                                await msg1.edit(embed=queueEmbed)
                                await msg1.clear_reactions()
                            except KeyError as e:
                                print(e)
                                await msg2.edit("The above arrows no longer work...")
                                await msg1.reply("Info is outdated. Recall queue command please!")
                            except Exception as e:
                                print(e)

        except discord.errors.HTTPException as e:
            print(e)
            await ctx.respond("Error with the Queue. Titles are too long. Contact Jakaroo14#7553, I need help!")
        except KeyError as e:
            print(e)
            await ctx.respond("Please play some songs first and make a queue!", ephemeral=True)
        except AttributeError as e:
            print(e)
            await ctx.respond("Please play some songs first and make a queue!", ephemeral=True)
        except Exception as e:
            print(e)
            print(type(e))
            await ctx.followup.send("Some error occurred...")
        finally:
            try:
                lock.release()
            except RuntimeError: # If lock was already released
                pass

        
        # ----------------------------------------
        # End of Queue
        # ----------------------------------------


    @commands.slash_command(description = helps['queues']['Shuffle'])
    async def shuffle(self, ctx):

        guild = ctx.guild.id

        await ctx.defer()

        try:
            await lock.acquire()

            length = len(songs[guild])

            if length > 2:
                random.shuffle(songs)
                await ctx.respond("Shuffled!")
            elif length == 2:
                await ctx.respond("Not enough songs in queue", ephemeral=True)
            else:
                await ctx.respond("Nothing in queue to shuffle", ephemeral=True)
        except Exception as e:
            print("Shuffle error")
            print(e)
        finally:
            try:
                lock.release()
            except RuntimeError: # If lock was already released
                pass

        # ----------------------------------------
        # End of Shuffle
        # ----------------------------------------


    @commands.slash_command(description = helps['queues']['Supershuffle'])
    async def supershuffle(self, ctx):
        
        await ctx.defer()

        try:
            await lock.acquire()
            await ss(ctx)
        except Exception as e:
            print(e)
            print(type(e))
            await ctx.followup.send("Some error occurred...")
        finally:
            try:
                lock.release()
            except RuntimeError: # If lock was already released
                pass

        # ----------------------------------------
        # End of Supershuffle
        # ----------------------------------------


    @commands.slash_command(description = helps['queues']['Loop'], aliases = ["l", "loopsong", "songloop", "ls", "sl"])
    async def loop(
        self, 
        ctx,
        *, arg : discord.Option(name="value", description="(optional) Value to set loop to. True/False/On/Off. If no input, changes loop automatically", default=None) # type: ignore
        ):

        true = ["yes", "true", "y", "on"]
        voice[ctx.guild.id] = get(self.bot.voice_clients, guild=ctx.guild)
        if voice[ctx.guild.id] and voice[ctx.guild.id].is_playing():
            if arg != None:
                if arg.lower().strip() in true:
                    loopSong[ctx.guild.id] = True
                    await ctx.respond("Looping song")
                else:
                    loopSong[ctx.guild.id] = False
                    await ctx.respond("Song is no longer looped")
            elif loopSong[ctx.guild.id] == False:
                loopSong[ctx.guild.id] = True
                await ctx.respond("Looping song")
            else:
                loopSong[ctx.guild.id] = False
                await ctx.respond("Song is no longer looped")
        else:
            await ctx.respond("Please play a song first", ephemeral=True)
        # ----------------------------------------
        # End of Loop
        # ----------------------------------------


    @commands.slash_command(description = helps['queues']['Loopqueue'], aliases = ["queueloop", "ql", "lq"])
    async def loopqueue(
        self,
        ctx,
        *, arg : discord.Option(name="value", description="(optional) Value to set loop to. True/False/On/Off. If no input, changes queueloop automatically", default=None) # type: ignore
        ):

        true = ["yes", "true", "y"]
        voice[ctx.guild.id] = get(self.bot.voice_clients, guild=ctx.guild)
        if voice[ctx.guild.id] and voice[ctx.guild.id].is_playing():
            if arg != None:
                if arg.lower().strip() in true:
                    loopQueue[ctx.guild.id] = True
                    await ctx.respond("Looping queue")
                else:
                    loopQueue[ctx.guild.id] = False
                    await ctx.respond("Queue is no longer looped")
            elif loopQueue[ctx.guild.id] == False:
                loopQueue[ctx.guild.id] = True
                await ctx.respond("Looping queue")
            else:
                loopQueue[ctx.guild.id] = False
                await ctx.respond("Queue is no longer looped")
        else:
            await ctx.respond("Please play a song first", ephemeral=True)
        # ----------------------------------------
        # End of Loopqueue
        # ----------------------------------------


    @commands.slash_command(description = helps['queues']['Clear_Copies'], aliases = ["cc", "clear", "c"])
    async def clear_copies(self, ctx):
        guild = ctx.guild.id
        removed = 0

        # Checks if command can be called
        if len(songs[guild]) <= 1:
            await ctx.respond("Not enough songs to test!", ephemeral=True)
            return


        def find_indices(list, term):
            '''Returns a list of the indices of the term found inside a list'''
            return [index for (index, item) in enumerate(list) if item.url == term]


        def pop_at(index):
            '''Removes all components of a song at a given index'''
            songs[guild].pop(index)

        await ctx.defer()

        try:
            await lock.acquire()
            # Performs clearing of copies for all songs in songs[guild]
            for song in songs[guild]:
                indices = find_indices(songs[guild], song.url)
                if len(indices) > 1:
                    indices.reverse()
                    for x in range(0, len(indices)-1):
                        pop_at(indices[x])
                        removed += 1

            
            # Respond when done
            await ctx.respond(f"Removed all copies! Total of {removed} songs removed!")
        except Exception as e:
            print(e)
            print(type(e))
            await ctx.followup.send("Some error occurred...")
        finally:
            try:
                lock.release()
            except RuntimeError: # If lock was already released
                pass
    
        # ----------------------------------------
        # End of Clear_copies
        # ----------------------------------------
                    

    

def setup(bot):
    bot.add_cog(queues(bot))
