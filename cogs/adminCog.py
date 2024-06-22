import logging
import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import TextInput
from cogs.group import organize_group as og
from config import DATA, settings, messages as msg
from functools import wraps
from views.base import BaseModal


def devs_only(func):
    """Decorator to restrict interactions to users with id in settings['developers'].
    """
    print("WRAPPING SOMETHING")
    @wraps(func)
    async def wrapper(self, inter):
        print("CHECKING DEV PERMISSION")
        if inter.user.id not in settings.get("developers", []):
            await inter.response.send_message("Permission denied.", ephemeral=True)
            return
        return await func(self, inter)
    return wrapper

class AdminCog(commands.Cog):
    """A set of admin commands to manage the bot.
    All commands created for the group are accessable as `/admin command ...`.
    Most commands require administrator permissions (for guild where its called) or
    the user to be a developer (set in config/settings.yml)
    """
    group = app_commands.Group(name="admin", description="Admin commands") # guild_only=True

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    # @group.command(name="reload", description="Reloads data from file.")
    @group.command(name="reload", description="Reloads data from file.")
    @devs_only
    async def reload(self, inter):
        print("RELOADING")
        og.load_data()
        await inter.response.send_message("Data reloaded.")

    @group.command(name="download", description="Dev: Download log file and guilds.yml")
    @devs_only
    async def download(self, inter):
        # if inter.user.id not in settings.get("developers", []):
        #     await inter.response.send_message("Permission denied.", ephemeral=True)
        #     return
        await inter.user.send(file=discord.File(DATA/"discord.log"))
        await inter.user.send(file=discord.File(DATA/"guilds.yml"))
        await inter.response.send_message("Files sent.")

    @group.command(name="removechannels", description="Dev: Remove all channels.")
    @devs_only
    async def removechannels(self, inter: Interaction, but: str=None):
        """Remove all channels in the guild.
        @param but: string of channel names to exclude from removal.
        """
        removed = []
        for channel in inter.guild.channels:
            if but and channel.name.lower() in but.lower():
                logging.debug("didnt remove channel %s", channel.name)
                continue
            cname = f"{channel.name}"
            await channel.delete()
            removed.append(cname)
        inter.response.send_message(f"Channels removed: {', '.join(removed)}")
    
    @group.command(name="removeroles", description="Dev: Remove all roles.")
    @devs_only
    async def removeroles(self, inter, but: str=None):
        """Remove all roles in the guild.
        @param but: string of role names to exclude from removal.
        """
        removed = []
        for role in inter.guild.roles:
            if but and role.name.lower() in but.lower():
                logging.debug("didnt remove role %s", role.name)
                continue
            try:
                rname = f"{role.name}"
                await role.delete()
                removed.append(rname)
            except:
                pass
        await inter.response.send_message(f"Roles removed: {', '.join(removed)}")
    
    @app_commands.command(name="bug", description="Report a bug or other issues.")
    async def bug(self, inter):
        await inter.response.send_modal(BugForm())

    # NOTE: decorator example for only allowing command to be run in guilds (not dms)
    # @app_commands.guild_only()  # can also be used as class decorator for groups 
    # async def gadd(self, ctx, group: str, player: discord.Member):
    #     group = Group.load(group, ctx=ctx)
    #     await group.add_player(player.id)
    #     await ctx.reply(f"Added <@{player.id}> to {group.name}")
        

    # # TODO: should be admin command:
    # @command()

class BugForm(BaseModal):
    title = TextInput(
        label=msg["name_la"], placeholder=msg["name_ph"], min_length=1, max_length=80
    )
    text = TextInput(
        label=msg["text_la"],
        placeholder=msg["text_ph"],
        required=False,
        max_length=1400,
        min_length=0,
        style=discord.TextStyle.long,
    )

    async def on_submit(self, inter: Interaction) -> None:
        # await super().on_submit(interaction)
        devs = settings.get("developers", [])
        if len(devs) == 0:
            await inter.response.send_message(msg["bug_nodev"], ephemeral=True)
            return
        for user in devs:
            await self.bot.get_user(user).send(
                f"Bug report from {inter.user.name}:\n**{self.title.value}**\n{self.text.value}"
            )
        await inter.response.send_message(msg["bug_reported"], ephemeral=True)