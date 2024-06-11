#!/usr/bin/env python3
import logging
import re

import discord
from discord.ext import commands
from discord.ext.commands import Context, Bot, parameter, Cog, command
from discord.utils import get
from config import messages as msg

from cogs.group import organize_group as og
from cogs.group.organize_group import Group
from utility.sanitizer import sanitize
from cogs.group.organize_group import NewGroupView


class GroupCommands(Cog):
    """ Commands for handling groups
    This cog contains all commands related to creating, managing and joining groups.
    All logic and data operations should be part of `group.organize_group.Group`.
    This class focus on handling the command itself (i.e. parsing parameters).
    TODO: we can add command specific error handling here too. i.e. 
    @gcreate.error
    async def gcreate_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Some required arguments are missing.')
        # other errors should be propagated to more general handler (needs to be tested)
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    @command(help=msg["gcreate_help"], aliases=['gneu'])
    async def gcreate(self, 
        ctx: Context, 
        name: str = parameter(description=msg["gcreate_group"]),
        time: str = parameter(
            default="",
            description=msg["gcreate_time"]),
        maximum_players: int = parameter(
            default=4,
            description=msg["gcreate_maxplayers"]
        ),
        description: str = parameter(
            default=msg["gcreate_desc_default"],
            description=msg["gcreate_desc"]
        )
    ):
        group = Group(
            name=name,  # slug generated from name
            date=time,
            max_players=maximum_players,
            description=description,
            ctx=ctx,  # sets owner and guild id
            bot=self.bot,
        )
        if group.exists:
            await ctx.reply(msg["gcreate_group_exists"].format(name=name), ephemeral=True)
            return
        group.save()  # writes to yaml
        await group.setup_guild()  # create role, category and channels
        await ctx.reply(msg["gcreate_success"].format(group=group), ephemeral=True)

    @gcreate.error
    async def gcreate_error(self, ctx, error):
        if (isinstance(error, commands.errors.MissingRequiredArgument) 
        or isinstance(error, commands.errors.BadArgument)):
            view = NewGroupView(ctx.author)
            view.bot = self.bot
            await ctx.send(msg["gcreate_bad_args"].format(
                pre=ctx.prefix, cmd=ctx.command.name, sig=ctx.command.signature
            ), view=view)
            raise commands.CommandInvokeError(error)  # prevent propagation

    @command(help=msg["glist_help"], aliases=['gliste'])
    async def glist(self, ctx, full: bool = parameter(
            default=False, description=msg["glist_desc"])
        ):
        await ctx.reply(msg["glist_header"])
        for group in Group.groups_from_guild(ctx.guild.id):
            group.message = await ctx.reply(group.info_message, view=group.info_view(ctx.author))

    async def delete_group(self, ctx, group_name):
        sanitized_guild = sanitize(ctx.guild.name)
        status, result_str, players, channels, category = og.destroy_group(sanitized_guild, group_name)
        # if status, delete channels and role
        if status:
            # remove role
            role = discord.utils.get(ctx.guild.roles, name=group_name)
            if role:
                await role.delete()
                logging.debug(f"Deleted role {role}.")

            # remove channels
            for channel_id in channels:
                tmp_channel = ctx.guild.get_channel(channel_id)
                if tmp_channel:
                    await tmp_channel.delete()
                    og.remove_channel(sanitized_guild, group_name, tmp_channel.id)
                    logging.debug(f"Deleted channel {tmp_channel.name}.")

            # remove category
            tmp_category = ctx.guild.get_channel(category)
            if tmp_category:
                await tmp_category.delete()
                logging.debug(f"Deleted category {tmp_category}.")
        for player_id in players:
            member = ctx.guild.get_member(player_id)
            await member.send(msg["group_deleted_info"].format(author=ctx.author, name=group_name))
        await ctx.reply(result_str)

    @command(help=msg["gdestroy_help"], aliases=['gentfernen'])
    async def gdestroy(
        self, ctx, 
        group_prefix: str = parameter(
            description=msg["group_prefix"]
        )
    ):
        sanitized_guild = sanitize(ctx.guild.name)
        group_name = sanitize(group_prefix)
        await self.delete_group(ctx, group_name)

    @command(
        help=msg["gpurge_help"],
        aliases=['gbereinigen'],
        hidden=True)

    @commands.has_permissions(administrator=True)
    async def gpurge(
        self, ctx, 
        group_name: str = parameter(
            description=msg["gpurge_group"]
        )
    ):
        await self.delete_group(ctx, group_name)

    @command(
        help=msg["gsetdate_help"],
        aliases=['gsetzedatum'])
    async def gsetdate(self, ctx, 
        group_prefix: str = parameter(description=msg["group_prefix"]),
        value: str = parameter(
            description=msg["gsetdate_value"])
    ):
        group = sanitize(group_prefix)
        result_str = og.set_key(sanitize(ctx.guild.name), group, og.DATE, value)
        await ctx.reply(result_str)

    @command(
        help=msg["gsetdescription_help"],
        aliases=['gsetzebeschreibung'])
    async def gsetdescription(
        self, ctx, 
        group: str = parameter(description=msg["gsetdescription_group"]),
        value: str = parameter(
            description=msg["gsetdescription_value"])
    ):
        group = sanitize(group)
        guild = sanitize(ctx.guild.name)
        # TODO: or admin.. add easier permission checks (pass context to group method)
        if not og.is_owner(guild, group, ctx.author.id):
            await ctx.reply(msg["not_owner"])
            return
        result_str = og.set_key(sanitize(ctx.guild.name), group, og.DESCRIPTION, value)
        await ctx.reply(result_str)

    @command(
        help=msg["gsetnumberofplayers_help"],
        aliases=['gsetzespieleranzahl'])
    async def gsetnumberofplayers(
        self, ctx,
        group_prefix: str = parameter(description=msg["group_prefix"]),
    value: str = parameter(
        description=msg["gsetnumberofplayers_value"])):
        group = sanitize(group_prefix)
        guild = sanitize(ctx.guild.name)
        if not og.is_owner(guild, group, ctx.author.id):
            await ctx.reply(msg["not_owner"])
            return
        result_str = og.set_key(guild, group, og.PLAYER_NUMBER, value)
        await ctx.reply(result_str)

    @command(help=msg["gremove_help"], aliases=['gkick'])
    async def gremove(
        self, ctx, 
        group: str = parameter(description=msg["group_prefix"]),
        player: discord.Member = parameter(description=msg["gremove_player"])
    ):
        group = sanitize(group)
        guild = sanitize(ctx.guild.name)
        if not og.is_owner(guild, group, ctx.author.id):
            await ctx.reply(msg["not_owner"])
            return
        status, result_str = og.remove_player(guild, group, player.id)
        if status:
            group_role = get(ctx.guild.roles, name=group)
            # removing group role when existing
            if group_role in player.roles:
                await player.remove_roles(group_role)
                logging.debug(f"Removed role {group_role} from user {player}.")
            text_channel = ctx.guild.get_channel(og.get_main_channel(sanitize(ctx.guild.name), group))
            await text_channel.send(msg["gremove_info"].format(player=player.id))

        await ctx.reply(result_str)

    @command(help=msg["gjoin_help"], aliases=['gbeitreten'])
    async def gjoin(self, ctx, 
        group: str = parameter(description=msg["gjoin_group"])
    ):
        group = re.sub('[^0-9a-zA-Z\-_]+', '', group.replace(" ", "-")).lower()

        if og.is_owner(sanitize(ctx.guild.name), group, ctx.author.id):
            status, result_str = False, msg["join_own_group"]
        else:
            status, result_str = og.add_self(sanitize(ctx.guild.name), group, ctx.author.id)

        if status:
            # get the role by group name
            group_role = get(ctx.guild.roles, name=group)
            await ctx.author.add_roles(group_role)
            logging.debug(f"Added role {group_role} to user {ctx.author}.")
            text_channel = ctx.guild.get_channel(og.get_main_channel(sanitize(ctx.guild.name), group))
            await text_channel.send(msg["gjoin_info"].format(player=ctx.author.id))

        await ctx.reply(result_str)

    @command(help=msg["gleave_help"], aliases=['gaustreten'])
    async def gleave(
        self, ctx, 
        group: str = parameter(
            description=msg["gleave_group"]
        )
    ):
        # TODO: can we use sanitize() here?
        group = re.sub('[^0-9a-zA-Z\-_]+', '', group.replace(" ", "-")).lower()
        status, result_str = og.remove_self(sanitize(ctx.guild.name), group, ctx.author.id)

        if status:
            group_role = get(ctx.guild.roles, name=group)
            # removing group role when existing
            user_roles = ctx.author.roles
            if group_role in user_roles:  # only remove if role really exists
                await ctx.author.remove_roles(group_role)
                logging.debug(f"Removed role {group_role} from user {ctx.author}.")
            text_channel = ctx.guild.get_channel(og.get_main_channel(sanitize(ctx.guild.name), group))
            await text_channel.send(msg["gremove_info"].format(player=ctx.author.id))

        await ctx.reply(result_str)

    @command(help=msg["gaddchannel_help"],
                      aliases=['gchannelhinzufügen'])
    async def gaddchannel(
        self, ctx, group_prefix: str = parameter(description=msg["group_prefix"]),
        channel_name: str = parameter(
            description=msg["gaddchannel_channel"]),
        is_voice: bool = parameter(
            default=False,
            description=msg["gaddchannel_voice"])
    ):
        # TODO: only allow for gm or for everyone?
        group_name = sanitize(group_prefix)
        sanitized_guild = sanitize(ctx.guild.name)
        category = discord.utils.get(ctx.guild.categories, name=group_name)

        # Handle Roles
        everyone = ctx.guild.default_role
        role = discord.utils.get(ctx.guild.roles, name=group_name)
        overwrites = {everyone: discord.PermissionOverwrite(read_messages=False),
                      role: discord.PermissionOverwrite(read_messages=True)}

        # Add Channel
        if is_voice:
            voice_channel = await ctx.guild.create_voice_channel(
                name=channel_name, 
                overwrites=overwrites,
                category=category
            )
            og.add_channel(sanitized_guild, group_name, voice_channel.id)
            logging.debug(f"Created voice channel {voice_channel}")
            await ctx.reply(msg["gaddchannel_created_voice"])
        else:
            text_channel = await ctx.guild.create_text_channel(
                name=channel_name, 
                overwrites=overwrites,
                category=category
            )
            og.add_channel(sanitized_guild, group_name, text_channel.id)
            logging.debug(f"Created text channel {text_channel}")
            await ctx.reply(msg["gaddchannel_created_text"])
