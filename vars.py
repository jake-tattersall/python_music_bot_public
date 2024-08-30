import asyncio
import os
import re
from datetime import timedelta

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Gets Bot Token from Local File
load_dotenv(".env")
TOKEN = os.getenv("DISCORD_TOKEN")

# Sets Bot Command Prefix
bot = commands.Bot(command_prefix = "%", case_insensitive=True, intents=discord.Intents.all())
bot.help_command = None

# For dict management
lock = asyncio.Lock()

# For Song Queue, loop commands, shuffle, etc. 
voice = {}
loopSong = {}
loopQueue = {}
songs = {}


server_indep_vars = {
    'word' : None,
    'definition' : None,
}


helps = {
    'playing' : {
        'Astley' : "Never gonna give you up, Never gonna let you down...",
        'Leave' : "Forces Bot to Leave the Call",
        'Lofi' : "Plays the Lofi Girl livestream",
        'Play' : "Looks at YouTube for the given link or keyword(s), then plays it or adds it to queue",
        'Playlist' : "Plays a YouTube playlist. You must enter a link, you cannot search for a playlist using this",
        'Stop' : "Stops playing music. Removes Queue"
    },

    'queues' : {
        'Clear_Copies' : "Removes all copies of songs in the queue",
        'Loop' : "Loops the current song being played",
        'Loopqueue' : "Loops the queue",
        'Queue' : "Displays the queue. You can also specify which page to view",
        'Remove' : "Removes specified song from the queue",
        'Shuffle' : "Shuffles the queue",
        'Supershuffle' : "Shuffle, but better? Works best with 3+ songs. Avoid use while songs are being added to queue",
        'Skip' : "Skips the song currently playing and plays the next song if available"
    },

    'miscellaneous' : {
        'Blackjack' : "Not yet implemented",
        'Coinflip' : "Flips a coin, with results of heads or tails.",
        'Diceroll' : "Rolls a die. If no number of sides are specified, rolls a 6-sided die.",
        'Ping' : "Ping Pong Ping Pong",
        'Rps' : "Challenge someone to Rock Paper Scissors!",
        'Word' : "Get the definition of the word of the day, or the bot's status"
    }
}


# For playing songs

def remove_color_codes(text):
    # Define a regular expression pattern to match ANSI escape codes
    ansi_escape_pattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    # Use the pattern to substitute escape codes with an empty string
    return ansi_escape_pattern.sub('', text)

class loggerOutputs:
  def error (message):
    pass
  def warning (message):
    print(message)
  def debug (message):
    message = remove_color_codes(message)
    if "[download] Downloading item" in message:
        message = message.split(" ")
        current = message[3]
        total = message[5]
        print(message, current, total)

# Options passed to yt-dlp 
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
ydl_opts = {
    'format':'bestaudio/best',
    'postprocessors': [{
        'key':'FFmpegExtractAudio',
    }],
    'quiet':True,
    'cookies':os.getenv("COOKIEFILE"),
    'usenetrc':True,
    'logger':loggerOutputs,
    }

# Color for embeds
color = 0XFFDACF


class DurationError(Exception):
    """Specifies that the song is too long"""

class YTDLParsingError(Exception):
    """Rasied when the info of duration, title, formats, etc. has changed or is not present"""


class Song():
    def __init__(self):
        self.title : str = None
        self.duration_int : int = None
        self.duration_dt : str = None
        self.url : str = None
        self.thumbnail : str = None
        self.addedby : discord.User = None
        self.info : dict = None
        self.idx : int = None


    async def fillSongData(self, arg, info, ytsearch) -> None:
        """
        Generates values for title, duration, url, and thumbnail. Also saves the info

        Raises YTDLParsingError if could not parse into the necessary values.

        Raises DurationError if longer than 3 hours.
        """
        self.info = info

        try:
            # Get video stats
            self.idx = self.getFormat()

            if not ytsearch:
                if info.get('is_live'):
                    dur = 0
                else:
                    dur = info['duration']

                if dur > 10800:
                    raise DurationError()

                self.url = info['webpage_url']
                self.thumbnail = info['thumbnail']
                self.duration_int = dur
                self.duration_dt = str(timedelta(seconds=dur))
                self.title = self.formatTitle(info['title'])
            else:
                if info['entries'][self.idx].get('is_live'):
                    dur = 0
                else:
                    dur = info['entries'][self.idx]['duration']            

                self.url = info['entries'][self.idx]['webpage_url']
                self.thumbnail = info['entries'][self.idx]['thumbnail']
                self.duration_int = dur
                self.duration_dt = str(timedelta(seconds=dur))
                self.title = self.formatTitle(info['entries'][self.idx]['title'])
            
        except:
            raise YTDLParsingError()
        else:
            if self.duration_int > 10800:
                raise DurationError()  


    def formatTitle(self, title) -> str:
        '''Returns the video's title from youtube-dl source info'''
        if self.duration_int == 0:
            title = title[0:-16]

        title = title.replace("\\", "\\\\").replace('"', '\\"').replace("*", "\*").replace("_", "\_").replace("~", "\~").replace(">", "\>")

        return title
    

    def getURL(self) -> None:
        '''Returns the url of the best format/entry. Performs idx searching inside'''
        try:
            url = self.info['formats'][self.idx]['url']
        except:
            url = self.info['entries'][self.idx]['url']

        return url
    


    def getFormat(self) -> int:
        '''Returns the index of an audio format.'''
        try:
            subinfo = self.info['formats']
        except:
            subinfo = self.info['entries']

        formatidx = -1
        for j in range(0, len(subinfo)):
            if "storyboard" in subinfo[j]['format_note'] or "sb" in subinfo[j]['format_id']:
                continue
            formatidx = j
            break

        return formatidx
