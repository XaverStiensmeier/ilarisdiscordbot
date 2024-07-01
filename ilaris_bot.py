#!/usr/bin/env python3
import traceback
import logging
import logging.handlers
import discord
from discord.ext import commands
from discord.ext.commands import after_invoke

import config
from config import DATA
from config import messages as msg
from cogs.generalCog import GeneralCommands
from cogs.group.organize_group import GroupSelect, Group
from cogs.groupsCog import GroupCommands
from cogs.adminCog import AdminCog
from cogs.onlineCog import OnlineCog
from views.base import BaseView
from utility.sanitizer import sanitize

import typing

# TODO: not sure where this belongs:
NO_UPDATE_COMMAND_LIST = ["glist"]

cfg = config  # TODO remove me
msg = cfg.messages

handler = logging.handlers.RotatingFileHandler(
    filename=DATA/'discord.log', 
    encoding='utf-8', 
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
log = logging.getLogger('discord')

# NOTE: all mentions are disabled by default (links work but without ping)
bot = commands.Bot(
    command_prefix='!',
    intents=discord.Intents().all(),
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True)
)


# Startup Information
@bot.event
async def on_ready():
    print('Connected to bot: {}'.format(bot.user.name))
    print('Bot ID: {}'.format(bot.user.id))
    await bot.add_cog(GeneralCommands(bot))
    await bot.add_cog(GroupCommands(bot))
    await bot.add_cog(AdminCog(bot))
    await bot.add_cog(OnlineCog(bot))
    await bot.tree.sync()  # sync command tree with discord api

@bot.event
async def on_message(ctx):
    try:
        await bot.process_commands(ctx)
    except Exception as e:
        print(e)
        log.error(e)

@bot.event
async def on_command_error(ctx, error):
    if ctx.command and ctx.command.has_error_handler():
        return  # Do not handle commands that have their own handler
    logging.debug(traceback.format_exc())
    if isinstance(error, commands.CommandNotFound):
        response = config.commands.get(ctx.invoked_with, {}).get("reply")
        if response:
            await ctx.send(response)
            return
        else:
            await ctx.send(msg["cmd_not_found"])
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(msg["bad_args"].format(
            pre=ctx.prefix, cmd=ctx.command.name, sig=ctx.command.signature
        ))
    elif isinstance(error, commands.errors.BadArgument):
        await ctx.send(msg["bad_args"].format(
            pre=ctx.prefix, cmd=ctx.command.name, sig=ctx.command.signature
        ))
    elif isinstance(error, Exception):
        if ctx.command:
            info = f"{bot.command_prefix}{ctx.command.name}: {ctx.command.help}"
        else:
            info = msg["unexpected_error"]
        await ctx.send(msg["cmd_failed"].format(info=info))
        raise error


@bot.event
async def on_command_completion(ctx):
    if ctx.guild:
        msg = "'{}' used '{}' on '{}' in '{}'"
        log.info(
            msg.format(ctx.author, ctx.message.content, ctx.guild.name, ctx.channel.name)
        )
    if (ctx.command.cog_name == "GroupCommands" 
        and ctx.command.name not in NO_UPDATE_COMMAND_LIST):
        channel = discord.utils.get(ctx.guild.text_channels,
            name=config.settings.get("groups_channel"))
        if channel:
            # TODO: move this "info channel" update to groups and add a function to set it
            await channel.purge()
            for result_str in Group.groups_from_guild(ctx.guild.id):
                await channel.send(result_str)
        else:
            log.info("No group channel found.")


@bot.event
async def on_reaction_add(reaction, user):
    log.warning("Reaction added")
    # Check if the reaction is on the bot's message and the emoji is the delete emoji
    if (reaction.message.author == bot.user 
        and reaction.emoji == "❌" 
        and user.guild_permissions.administrator
        and user != bot.user):
        # Delete the message
        await reaction.message.delete()


async def setup_hook() -> None:  # automatically called before the bot starts
    await bot.tree.sync()   # sync slash cmds with Discord mandatory for slash commands


# NOTE: no app command to manually resync app commands
@bot.command()
async def sync(ctx: commands.Context) -> None:
    """Sync commands"""
    synced = await ctx.bot.tree.sync()
    await ctx.send(f"Synced {len(synced)} commands globally")

@bot.tree.context_menu(name="invite")
async def invite(inter: discord.Interaction, member: discord.Member) -> None:
    embed = discord.Embed(title=member.name, description=f"{member.mention} is cool", color=member.color)
    embed.set_thumbnail(url=member.display_avatar)
    print("invite pressed")
    # groups = Group.groups_of_user(inter.user, owner=True)
    # print([g.name for g in groups])
    # print(groups)
    # menu = InviteMenu(inter.user)
    menu = BaseView(inter.user)
    menu.add_item(GroupSelect(inter.user, member))
    await inter.response.send_message(embed=embed, view=menu)

@bot.tree.context_menu(name="promote")
async def promote(inter: discord.Interaction, member: discord.Member) -> None:
    print("promote pressed")
    await inter.response.send_message(f"Promoted {member.mention}")

bot.run(config.settings["token"], log_handler=None)
