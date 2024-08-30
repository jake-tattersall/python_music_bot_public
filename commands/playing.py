import discord
from discord.ext import commands
from discord.utils import get

from methods import (checkArg, checkCtx, createPlayNexts, firstPlay, getSong,
                     getSongs, reset)
from vars import (DurationError, YTDLParsingError, color, helps, lock, songs,
                  voice)

# ----------------------------------------
# Beginning of playing.py
# ----------------------------------------

class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.slash_command(description = helps['playing']['Stop'])
    async def stop(self, ctx):
        '''Stops music playing and removes all queues'''
        try:
            if voice[ctx.guild.id].is_playing():
                reset(ctx.guild.id)
                voice[ctx.guild.id].stop()
                await ctx.respond("I stopped playing")
            else:
                await ctx.respond("I am not playing anything at the moment.", ephemeral=True)
        except:
            await ctx.respond("I am not playing anything at the moment.", ephemeral=True)

        # ----------------------------------------
        # End of Stop
        # ----------------------------------------


    @commands.slash_command(description = helps['playing']['Leave'])
    async def leave(self, ctx):
        '''Forces bot to leave the call. Removes queue'''
        try:
            reset(ctx.guild.id)
            await voice[ctx.guild.id].disconnect()
            voice[ctx.guild.id].cleanup()
            voice[ctx.guild.id] = None
            await ctx.respond("I left the call", ephemeral=True)
        except:
            await ctx.respond("I am not connected.", ephemeral=True)

        # ----------------------------------------
        # End of Leave
        # ----------------------------------------


    @commands.slash_command(description = helps['playing']['Astley'])
    async def astley(self, ctx):
        '''Plays "Never Gonna Give You Up" by Rick Astley'''
        astley = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # Error handling
        if not checkCtx(ctx):
            await ctx.respond("Please enter a voice channel first.", ephemeral=True)
            return
        
        await ctx.defer() 

        guild = ctx.guild.id
        voice[guild] = get(self.bot.voice_clients, guild=ctx.guild)     # Gets the voice channel

        try:
            song = await getSong(astley, ctx)
            
            await firstPlay(ctx, song)
            songs[guild].append(song)

            await ctx.followup.send("https://tenor.com/view/rick-roll-rick-ashley-never-gonna-give-you-up-gif-22113173")
            await ctx.send("Get Rickrolled")

            createPlayNexts(ctx)

        except DurationError:
            await ctx.followup.send("An unexpected error! This song is usually not long!", ephemeral=True)
            return
        except YTDLParsingError:
            await ctx.followup.send("Some error collecting data from the song. Contact Jakaroo14.", ephemeral=True)
            return
        except Exception as e:
            print(e)

        # ----------------------------------------
        # End of Astley
        # ----------------------------------------
            

    @commands.slash_command(description = helps['playing']['Lofi'])
    async def lofi(self, ctx):
        '''Plays "Never Gonna Give You Up" by Rick Astley'''
        lofi = "https://youtu.be/jfKfPfyJRdk"

        # Error handling
        if not checkCtx(ctx):
            await ctx.respond("Please enter a voice channel first.", ephemeral=True)
            return
        
        await ctx.defer() 

        guild = ctx.guild.id
        voice[guild] = get(self.bot.voice_clients, guild=ctx.guild)     # Gets the voice channel

        try:
            song = await getSong(lofi, ctx)

            await firstPlay(ctx, song)
            songs[guild].append(song)

            await ctx.followup.send("Time to relax...")

            createPlayNexts(ctx)

        except DurationError:
            await ctx.followup.send("An unexpected error! This song is usually not timed!", ephemeral=True)
            return
        except YTDLParsingError:
            await ctx.followup.send("Some error collecting data from the song. Contact Jakaroo14.", ephemeral=True)
            return
        except Exception as e:
            print(e)

        # ----------------------------------------
        # End of Lofi
        # ----------------------------------------


    @commands.slash_command(
        description = helps['playing']['Play'],
        aliases = ["p"])
    async def play(
        self,
        ctx, 
        *, arg : discord.Option(name="search_or_link", description="Keyword(s) or link to search for", required=True) # type: ignore
        ):

        '''Plays music based on user search or url given. Works most of the time, can play livestreams. Calls PlayNext at the end to test for queue'''

        #Error Handling
        if not checkCtx(ctx):
            await ctx.respond("Please enter a voice channel first.", ephemeral=True)
            return

        if not checkArg(arg):
            await ctx.respond("Please make sure to input a valid search or link.", ephemeral=True)
            return
        

        arg = arg.replace("'","").replace('"',"").strip()

        await ctx.defer()

        responded = False
        guild = ctx.guild.id


        try:
            await lock.acquire()
            # Get song
            toPlay = await getSongs(arg, ctx)
            song = toPlay[0]

            # Play song and send embed
            if voice[guild] != None and voice[guild].is_playing() and len(songs[guild]) >= 1:
                addedEmbed = discord.Embed(color=color)
                if song.duration_int == 0:
                    addedEmbed.add_field(name=f"Added to Queue", value= "**[" + song.title + "](" + song.url + ")** | `Livestream` | `Queue Position: " + str(len(songs[guild])) + "`")
                else:
                    addedEmbed.add_field(name=f"Added to Queue", value= "**[" + song.title + "](" + song.url + ")** | `Duration: " + song.duration_dt + "` | `Queue Position: " + str(len(songs[guild])) + "`")
                addedEmbed.set_thumbnail(url = song.thumbnail)
                addedEmbed.set_footer(text=f"Added by {song.addedby} | Songs added : {len(toPlay)}")
                                
                # Add song to queue
                songs[guild].extend(toPlay)

                await ctx.send(embed=addedEmbed)
                responded = True
            else:
                await firstPlay(ctx, song)
                songs[guild].extend(toPlay)
                
                playEmbed = discord.Embed(color=color)
                if song.duration_int == 0:
                    playEmbed.add_field(name="Now Playing:", value= "**[" + song.title + "](" + song.url + ")** | `Livestream`")
                else:
                    playEmbed.add_field(name="Now Playing:", value= "**[" + song.title + "](" + song.url + ")** | `Duration: " + song.duration_dt + "`\n")
                playEmbed.set_thumbnail(url = song.thumbnail)
                playEmbed.set_footer(text=f"Added by {song.addedby} | Songs added : {len(toPlay)}")
                await ctx.send(embed=playEmbed)
                responded = True

                await createPlayNexts(ctx)

        except DurationError:
            await ctx.followup.send("Song cannot be more than 3 hours. Try another link/search.", ephemeral=True)
            responded = True
            return
        except YTDLParsingError:
            await ctx.followup.send("Some error collecting data from the song. Contact Jakaroo14.", ephemeral=True)
            responded = True
            return
        except Exception as e:
            print(e)
            print(type(e))
            await ctx.followup.send("Some error occurred...")
            responded = True
        finally:
            if not responded:
                await ctx.followup.send("Try again. Something wrong happened.", ephemeral=True)
            try:
                lock.release()
            except RuntimeError: # If lock was already released
                pass


        # ----------------------------------------
        # End of Play
        # ----------------------------------------


def setup(bot):
    bot.add_cog(music(bot))