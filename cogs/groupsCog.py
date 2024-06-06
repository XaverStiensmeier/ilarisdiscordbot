#!/usr/bin/env python3
import logging
import re

import discord
from discord.ext import commands
from discord.utils import get
from config import messages as msg

from cogs.group import organize_group as og
from utility.sanitizer import sanitize


class GroupCommands(commands.Cog):
    """
    Commands for handling groups
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help=msg["gcreate_help"], aliases=['gneu'])
    async def gcreate(self, ctx, 
        group: str = commands.parameter(description=msg["gcreate_group"]),
        time: str = commands.parameter(description=msg["gcreate_time"]),
        maximum_players: int = commands.parameter(
            default=4,
            description=msg["gcreate_maxplayers"]
        ),
        description: str = commands.parameter(
            default=msg["gcreate_desc_default"],
            description=msg["gcreate_desc"]
        )
    ):
        group_name = sanitize(group)
        sanitized_guild = sanitize(ctx.guild.name)
        everyone = ctx.guild.default_role

        if og.group_exists(sanitized_guild, group_name):
            await ctx.reply(msg["gcreate_group_exists"].format(name=group_name))
            return
        # create role
        role = await ctx.guild.create_role(name=group_name)
        logging.debug(f"Created role {role}.")
        # add role to GM
        await ctx.author.add_roles(role)
        logging.debug(f"Added role {role} to user {ctx.author}.")
        # permissions
        overwrites = {everyone: discord.PermissionOverwrite(read_messages=False),
                        role: discord.PermissionOverwrite(read_messages=True)}
        logging.debug(f"Permission for role {role} set.")
        # create category
        category = await ctx.guild.create_category(name=group_name)
        logging.debug(f"Created category {category}")
        result_str = og.create_group(sanitized_guild, group_name, ctx.author.id, 
            category.id, time, maximum_players, description)
        # create channels
        text_channel = await ctx.guild.create_text_channel(name="Text", 
            overwrites=overwrites, category=category)
        og.add_channel(sanitized_guild, group_name, text_channel.id)
        logging.debug(f"Created text channel {text_channel}")

        voice_channel = await ctx.guild.create_voice_channel(
            name="Voice", overwrites=overwrites, category=category)
        og.add_channel(sanitized_guild, group_name, voice_channel.id)
        logging.debug(f"Created voice channel {voice_channel}")
        logging.debug("Added group.")
        await text_channel.send(msg["gcreate_channel_created"].format(
            author=ctx.author.id))
        await ctx.reply(result_str)

    @commands.command(help=msg["glist_help"], aliases=['gliste'])
    async def glist(self, ctx, full: bool = commands.parameter(
        default=False, description=msg["glist_desc"])
    ):
        for result_str in og.list_groups(sanitize(ctx.guild.name), full):
            await ctx.reply(result_str)

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

    @commands.command(help=msg["gdestroy_help"], aliases=['gentfernen'])
    async def gdestroy(
        self, ctx, 
        group_prefix: str = commands.parameter(
            description=msg["group_prefix"]
        )
    ):
        sanitized_guild = sanitize(ctx.guild.name)
        group_name = sanitize(group_prefix)
        await self.delete_group(ctx, group_name)

    @commands.command(
        help=msg["gpurge_help"],
        aliases=['gbereinigen'],
        hidden=True)
    @commands.has_permissions(administrator=True)
    async def gpurge(
        self, ctx, 
        group_name: str = commands.parameter(
            description=msg["gpurge_group"]
        )
    ):
        await self.delete_group(ctx, group_name)

    @commands.command(help=msg["gset_help"], aliases=['gsetze'])
    async def gset(
        self, ctx, 
        group_prefix: str = commands.parameter(
            description=msg["group_prefix"]
        ),
        key: str = commands.parameter(
            description=msg["gset_key"].format(
                date=og.DATE,
                players=og.PLAYER_NUMBER,
                description=og.DESCRIPTION
        )),
        value: str = commands.parameter(
            description=msg["gset_value"])):
        group = sanitize(group_prefix)
        result_str = og.set_key(sanitize(ctx.guild.name), group, key, value)
        await ctx.reply(result_str)

    @commands.command(
        help=msg["gsetdate_help"],
        aliases=['gsetzedatum'])
    async def gsetdate(self, ctx, 
        group_prefix: str = commands.parameter(description=msg["group_prefix"]),
        value: str = commands.parameter(
            description=msg["gsetdate_value"])
    ):
        group = sanitize(group_prefix)
        result_str = og.set_key(sanitize(ctx.guild.name), group, og.DATE, value)
        await ctx.reply(result_str)

    @commands.command(
        help=msg["gsetdescription_help"],
        aliases=['gsetzebeschreibung'])
    async def gsetdescription(
        self, ctx, 
        group: str = commands.parameter(description=msg["gsetdescription_group"]),
        value: str = commands.parameter(
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

    @commands.command(
        help=msg["gsetnumberofplayers_help"],
        aliases=['gsetzespieleranzahl'])
    async def gsetnumberofplayers(
        self, ctx,
        group_prefix: str = commands.parameter(description=msg["group_prefix"]),
    value: str = commands.parameter(
        description=msg["gsetnumberofplayers_value"])):
        group = sanitize(group_prefix)
        guild = sanitize(ctx.guild.name)
        if not og.is_owner(guild, group, ctx.author.id):
            await ctx.reply(msg["not_owner"])
            return
        result_str = og.set_key(guild, group, og.PLAYER_NUMBER, value)
        await ctx.reply(result_str)

    @commands.command(help=msg["gremove_help"], aliases=['gkick'])
    async def gremove(
        self, ctx, 
        group: str = commands.parameter(description=msg["group_prefix"]),
        player: discord.Member = commands.parameter(description=msg["gremove_player"])
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

    @commands.command(help=msg["gjoin_help"], aliases=['gbeitreten'])
    async def gjoin(self, ctx, 
        group: str = commands.parameter(description=msg["gjoin_group"])
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

    @commands.command(help=msg["gleave_help"], aliases=['gaustreten'])
    async def gleave(
        self, ctx, 
        group: str = commands.parameter(
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

    @commands.command(help=msg["gaddchannel_help"],
                      aliases=['gchannelhinzufügen'])
    async def gaddchannel(
        self, ctx, group_prefix: str = commands.parameter(description=msg["group_prefix"]),
        channel_name: str = commands.parameter(
            description=msg["gaddchannel_channel"]),
        is_voice: bool = commands.parameter(
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
