#!/usr/bin/env python3
import logging
import re

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context, Bot, param, Cog, command
from discord.utils import get
from config import messages as msg

from cogs.group import organize_group as og
from cogs.group.organize_group import Group
from utility.sanitizer import sanitize
from cogs.group.organize_group import NewGroupView
from views.base import BaseView


class GroupCommands(Cog):
    """ Commands for handling groups
    This cog contains all commands related to creating, managing and joining groups.
    All logic and data operations should be part of `group.organize_group.Group`.
    This class focus on handling the command itself (i.e. parsing parameters).
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    @command(help=msg["gcreate_help"], aliases=['gneu'])
    async def gcreate(self, 
        ctx: Context, 
        name: str = param(description=msg["gcreate_group"]),
        time: str = param(
            default="",
            description=msg["gcreate_time"]),
        maximum_players: int = param(
            default=4,
            description=msg["gcreate_maxplayers"]
        ),
        description: str = param(
            default=msg["gcreate_desc_default"],
            description=msg["gcreate_desc"]
        )
    ):
        group = Group(
            name=name,  # slug generated from name
            date=time,
            max_players=maximum_players,
            description=description,
            ctx=ctx,  # sets guild id
            owner=ctx.author.id,
            bot=self.bot,
        )
        if group.exists:
            await ctx.reply(msg["gcreate_group_exists"].format(name=name), ephemeral=True)
            return
        await group.setup_guild()  # create role, category and channels
        group.save()  # writes to yaml
        content = msg["gcreate_success"].format(group=group)
        buttons = group.info_view(ctx.author)
        group.message = await ctx.reply(content, view=buttons)

    @gcreate.error
    async def gcreate_error(self, ctx, error):
        if (isinstance(error, commands.errors.MissingRequiredArgument) 
        or isinstance(error, commands.errors.BadArgument)):
            view = NewGroupView(ctx.author)
            view.bot = self.bot
            await ctx.send(msg["gcreate_bad_args"].format(
                pre=ctx.prefix, cmd=ctx.command.name, sig=ctx.command.signature
            ), view=view)
            # raise commands.CommandInvokeError(error)  # prevent propagation

    @command(help=msg["glist_help"], aliases=['gliste'])
    async def glist(self, ctx, full: bool = param(
            default=False, description=msg["glist_desc"])
        ):
        await ctx.reply(msg["glist_header"])
        for group in Group.groups_from_guild(ctx.guild.id):
            group.bot = self.bot  # pass bot so group can fetch data form discord api.
            group.message = await ctx.reply(
                group.info_message, view=group.info_view(ctx.author))

    @command(help=msg["gedit_help"], aliases=['gbearbeiten'])
    async def gedit(self, ctx,
        group_name: str=param(description=msg["gedit_group_param"]),
        name: str=param(description=msg["gedit_name_param"], default=None),
        date: str=param(description=msg["gedit_date_param"], default=None),
        description: str=param(description=msg["gedit_desc_param"], default=None),
        max_players: int=param(description=msg["gedit_maxplayers_param"], default=None)
    ):
        try:
            group = Group.load(group_name, ctx=ctx)
        except ValueError as e:
            await ctx.reply(str(e))
            return
        if not group.is_owner(ctx.author.id):  # TODO: or admin
            await ctx.reply(msg["not_owner"])
            return
        if not date and not description and not max_players and not name:
            admin_view = group.admin_view()
            await ctx.reply(msg["gedit_no_args"], view=admin_view)
            return
        if date:
            group.date = date
        if description:
            group.description = description
        if max_players:
            group.max_players = max_players
        if date or description or max_players:
            group.save()
        if name:
            await group.rename(name)
        success = msg["gedit_success"].format(group=group) + "\n"
        success += msg["group_info"].format(group=group)
        await ctx.reply(success)
    
    @command(help=msg["gdestroy_help"], aliases=['gentfernen'])
    async def gdestroy(
        self, ctx, 
        name: str = param(description=msg["gdestroy_name_param"])
    ):
        try:
            group = Group.load(name, ctx=ctx)
            group.guild = ctx.guild.id  # only to support older data w/o guild ids
        except ValueError as e:
            await ctx.reply(msg["not_found"].format(name=name))
            await ctx.reply(str(e))
            return
        status, answer = await group.destroy(ctx.author)
        await ctx.reply(answer)

    # TODO: move to admin commands when available
    @command(
        help=msg["gpurge_help"],
        aliases=['gbereinigen'],
        hidden=True)
    @commands.has_permissions(administrator=True)
    async def gpurge(
        self, ctx, 
        group_name: str = param(
            description=msg["gpurge_group"]
        )
    ):
        await self.delete_group(ctx, group_name)


    @command(help=msg["gremove_help"], aliases=['gkick'])
    async def gremove(
        self, ctx, 
        group: str = param(description=msg["group_prefix"]),
        player: discord.Member = param(description=msg["gremove_player"])
    ):
        group = Group.load(group, ctx=ctx)
        status, result_str = await group.remove_player(player.id)
        await ctx.reply(result_str)

    @command(help=msg["gjoin_help"], aliases=['gbeitreten'])
    async def gjoin(self, ctx, 
        group_name: str = param(description=msg["gjoin_group"])
    ):
        # We could use directly group.add_player() here, the if clauses are only to
        # provide more detailed response messages.
        group = Group.load(group_name, ctx=ctx)
        if group.is_member(ctx.author):
            await ctx.reply(msg["gjoin_already"])
            return
        if len(group.players) >= group.max_players:
            await ctx.reply(msg["gadd_full"])
            return
        if group.is_owner(ctx.author):
            await ctx.reply(msg["gjoin_owner"])
            return
        status, answer = await group.add_player(ctx.author)
        await ctx.reply(answer)


    @command(help=msg["gleave_help"], aliases=['gaustreten'])
    async def gleave(
        self, ctx, 
        group_name: str = param(
            description=msg["gleave_group"]
        )
    ):
        group = Group.load(group_name, ctx=ctx)
        status, answer = await group.remove_player(ctx.author, check_owner=False)
        await ctx.reply(answer)
