import asyncio
import random

import discord
from discord.ext import commands

from vars import bot, color, helps, server_indep_vars


class misc(commands.Cog, name="misc"):
    def __init__(self, bot):
        self.bot = bot


    @commands.slash_command(description = "Get some help")
    async def help(
        self, 
        ctx,
        *, arg : discord.Option(str, name="command", description="(Optional) command name to get help on", default="") # type: ignore
        ):

        helpEmbed = discord.Embed(title="Commands", color=color)

        for cog, lists in helps.items():
            field = ""
            for command, desc in lists.items():
                if command.lower() == arg.strip().lower(): # If the user searched a command and one is found: break, create a new embed, and only add that field to it
                    single = discord.Embed(color=color)
                    single.add_field(name=command, value=desc)
                    break
                else:
                    field += f"`{command}` : {desc}\n"
            
            helpEmbed.add_field(name=cog.capitalize(), value=field, inline=False)

        # If single was made (a command was searched and found), send that. Else, send the full list.
        try:
            await ctx.respond(embed=single)
        except:
            await ctx.respond(embed=helpEmbed)

        # ----------------------------------------
        # End of Help
        # ----------------------------------------


    @commands.slash_command(description = helps['miscellaneous']['Ping'])
    async def ping(self, ctx):
        '''Ping Pong!'''
        await ctx.respond("Pong! `{0:.2f} ms`".format(self.bot.latency*1000))
        # ----------------------------------------
        # End of Ping
        # ----------------------------------------


    @commands.slash_command(description=helps['miscellaneous']['Coinflip'], aliases=["cf"])
    async def coinflip(self, ctx):

        num = random.randint(0, 1)
        if num == 0:
            await ctx.respond("It was heads!")
        else:
            await ctx.respond("It was tails!")

        # ----------------------------------------
        # End of Coinflip
        # ----------------------------------------
            

    @commands.slash_command(description=helps['miscellaneous']['Diceroll'], aliases=["dr", "dice", "d", "roll"])
    async def diceroll(
        self,
        ctx, 
        *, sides : discord.Option(description="(Optional) Number of sides. Autofills 6", default="6") # type: ignore
        ):

        # Test if 'sides' is an int and a positive int. If not, respond with error msg. If it is acceptable (default 6), send result
        try:
            sides = int(sides)
            if sides <= 0:
                await ctx.respond("Please use a valid number in number form!", ephemeral=True)
                return 
        except:
            await ctx.respond("Please use a valid number in number form!", ephemeral=True)
            return
        await ctx.respond("You rolled a `" + str(random.randint(1, sides)) + "` on a " + str(sides) + "-sided die!")

        # ----------------------------------------
        # End of Diceroll
        # ----------------------------------------


    @commands.slash_command(description=helps['miscellaneous']['Rps'])
    async def rps(
        self, 
        ctx, 
        *, target : discord.Option(discord.User, name="user", description="Person to challenge", required=True) # type: ignore
        ):

        if target == ctx.author:
            await ctx.respond("You cannot challenge yourself! Unless you have two brains, that would not be fair!", ephemeral=True)
            return

        # Logic used to determine winner
        async def compare(challengerChoice, targetChoice, msg):
            if challengerChoice == "Rock":
                if challengerChoice == targetChoice:
                    await msg.reply("You tied! You both picked Rock!")
                elif targetChoice == "Paper":
                    await msg.reply(f"{ctx.user} picked Rock. {target} picked Paper. \n{target.mention}You win!")
                else:
                    await msg.reply(f"{ctx.user} picked Rock. {target} picked Scissors. \n{ctx.user.mention}You win!")
            elif challengerChoice == "Paper":
                if challengerChoice == targetChoice:
                    await msg.reply("You tied! You both picked Paper!")
                elif targetChoice == "Scissors":
                    await msg.reply(f"{ctx.user} picked Paper. {target} picked Scissors. \n{target.mention}You win!")
                else:
                    await msg.reply(f"{ctx.user} picked Paper. {target} picked Rock. \n{ctx.user.mention}You win!")
            else:
                if challengerChoice == targetChoice:
                    await msg.reply("You tied! You both picked Scissors!")
                elif targetChoice == "Paper":
                    await msg.reply(f"{ctx.user} picked Scissors. {target} picked Paper. \n{ctx.user.mention}You win!")
                else:
                    await msg.reply(f"{ctx.user} picked Scissors. {target} picked Rock. \n{target.mention}You win!")

        class myView(discord.ui.View):

            def __init__(self):
                self.targetChoice = ""
                self.challengerChoice = ""
                super().__init__(timeout=60)


            async def on_timeout(self):
                self.disable_all_items()
                await self.message.edit(content=f"{ctx.user.mention} {target.mention} Someone took their time! Everything is disabled.", view=self)
            
            
            # Defines the select-menu in the view
            @discord.ui.select(
                placeholder="Rock, Paper, or Scissors",
                min_values=1,
                max_values=1,
                options = [
                    discord.SelectOption(
                        label="Rock",
                        description="Paper covers Rock smashes Scissor"
                    ),
                    discord.SelectOption(
                        label="Paper",
                        description="Scissor cuts Paper covers Rock"
                    ),
                    discord.SelectOption(
                        label="Scissors",
                        description="Rock smashes Scissors cuts Paper"
                    )
                ]
            )

            # Necessary function to decide what to do if any user interacts with the view
            async def select_callback(self, select, interaction):

                # Get user's selection
                userOpt = select.values[0]
                await interaction.response.send_message(f"You chose {userOpt}", ephemeral=True)

                # If the user is the challenger or challenge target, only then does some value get altered.
                if interaction.user == ctx.user:
                    self.challengerChoice = userOpt
                elif interaction.user == target:
                    self.targetChoice = userOpt

                # Once both the challenger and challenge target have made choices, stop listening for values and compare the result
                if self.challengerChoice != "" and self.targetChoice != "":
                    select.disabled = True
                    await self.message.edit(view=self)
                    self.stop()
                    await compare(self.challengerChoice, self.targetChoice, self.message)

        # Logic error handling for if the target is a bot and if the user exists
        async for person in ctx.guild.fetch_members():
            if target == person and target.bot == False:
                await ctx.respond(f"{target.mention}, {ctx.user.mention} has challenged you to Rock Paper Scissors!")
                msg1 = await ctx.send(view=myView())
                myView.message = msg1
                return
            elif target == person and target.bot == True:
                await ctx.respond(f"Oh, silly! {target.mention} is a bot! They can't answer back!", ephemeral=True)
                return

        await ctx.respond("No user with that @. Try @ing a different user.", ephemeral=True)
        return
    
        # ----------------------------------------
        # End of Rps
        # ----------------------------------------


    @commands.slash_command(description = helps['miscellaneous']['Word'])
    async def word(self, ctx):
        if server_indep_vars['definition'] == None:
            await ctx.respond("There is no word of the day.")
        else:
            await ctx.respond(f"The definition of {server_indep_vars['word']} is: `{server_indep_vars['definition']}`")
        
        # ----------------------------------------
        # End of Word
        # ----------------------------------------


    @commands.slash_command(description = "Command for owner only")
    async def vanilla(self, ctx):

        # If not me, send error message. Else, generate 3 digit num for verification.
        if ctx.author.id != 0: # Replace 0 with your discord id
            await ctx.respond("Sorry! You are not allowed to use this!", ephemeral=True)
        else:
            vanillaCode = random.randrange(100, 999)
            await ctx.respond("Are you sure? If so, type:" + '"' + str(vanillaCode) + '"')
            def check2(author):
                def inner_check2(msg):
                    return msg.author == author
                return inner_check2

            # Waits for a message from command caller (me), and if a response is given: Close is code matches, else send error msg
            try:
                msg = await self.bot.wait_for('message', timeout = 10, check = check2(ctx.author))
            except asyncio.TimeoutError:
                await ctx.send("Never mind...")
                return
            except Exception as e:
                print(e)
            else:
                if msg.content.strip() == str(vanillaCode):
                    await ctx.send("Good Bye!")
                    await bot.change_presence(status = discord.Status.offline)
                    await self.bot.close()
                    exit(1)
                else:
                    await ctx.send("Verification rejected.")
        # ----------------------------------------
        # End of Vanilla
        # ----------------------------------------


    @commands.slash_command(description="Command for owner only")
    async def tasks(self, ctx):
        if ctx.author.id != 427992974417199106:
            await ctx.respond("Sorry! You are not allowed to use this!", ephemeral=True)
            return
        
        try:
            tasks = []
            for task in asyncio.all_tasks():
                tasks.append(str(task))
            await ctx.respond(content="Here are the current tasks:\n" + "\n\n".join(tasks), ephemeral=True)
        except:
            await ctx.respond("Check console", ephemeral=True)
            print("Here are the current tasks:\n" + "\n\n".join(tasks))
        
        # ----------------------------------------
        # End of Tasks
        # ----------------------------------------
        
    


def setup(bot):
    bot.add_cog(misc(bot))