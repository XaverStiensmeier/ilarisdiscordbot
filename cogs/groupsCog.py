#!/usr/bin/env python3
import logging
import re

import discord
from discord.ext import commands
from discord.utils import get

from cogs.group import organize_group
from utility.sanitizer import sanitize_single, sanitize_group_name


class GroupCommands(commands.Cog):
    """
    Commands for handling groups
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Creates a new group with yourself as the GM.",
                      aliases=['gneu'])
    async def gcreate(self, ctx, group: str = commands.parameter(description="Your group to create"),
                      time: str = commands.parameter(
                          description="Time to play in GMT+1 (for example '24.02.24 14:00')"),
                      maximum_players: int = commands.parameter(
                          default=4, description="Maximum number of players"),
                      description: str = commands.parameter(default="Eine spannende Ilaris Runde!",
                                                            description="Description for your soon-to-be players")):
        group_name = sanitize_group_name(group, ctx.author)
        sanitized_guild = sanitize_single(ctx.guild)
        everyone = ctx.guild.default_role

        if not organize_group.group_exists(sanitized_guild, group_name):
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
            result_str = organize_group.create_group(sanitized_guild, group_name, ctx.author.id, category.id, time,
                                                     maximum_players, description)
            # create channels
            text_channel = await ctx.guild.create_text_channel(name="Text", overwrites=overwrites,
                                                               category=category)
            organize_group.add_channel(sanitized_guild, group_name, text_channel.id)
            logging.debug(f"Created text channel {text_channel}")

            voice_channel = await ctx.guild.create_voice_channel(name="Voice",
                                                                 overwrites=overwrites,
                                                                 category=category)
            organize_group.add_channel(sanitized_guild, group_name, voice_channel.id)
            logging.debug(f"Created voice channel {voice_channel}")

            logging.debug("Added group.")
            await text_channel.send(f"Hey, <@{ctx.author.id}>! Ich habe dir und deiner Gruppe diesen Kanal erstellt.")
            await ctx.reply(result_str)
        else:
            await ctx.reply(f"You already have a group called {group_name}...")

    @commands.command(help="Lists all joinable groups.", aliases=['gliste'])
    async def glist(self, ctx,
                    full: bool = commands.parameter(default=False, description="'True' to show full groups, too")):
        for result_str in organize_group.list_groups(sanitize_single(ctx.guild), full):
            await ctx.reply(result_str)

    async def delete_group(self, ctx, group_name):
        sanitized_guild = sanitize_single(ctx.guild)
        status, result_str, players, channels, category = organize_group.destroy_group(sanitized_guild, group_name)
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
                    organize_group.remove_channel(sanitized_guild, group_name, tmp_channel.id)
                    logging.debug(f"Deleted channel {tmp_channel.name}.")

            # remove category
            tmp_category = ctx.guild.get_channel(category)
            if tmp_category:
                await tmp_category.delete()
                logging.debug(f"Deleted category {tmp_category}.")
        for player_id in players:
            member = ctx.guild.get_member(player_id)
            await member.send(f"{ctx.author} hat die Gruppe {group_name} gelöscht. Du bist daher kein Mitglied mehr.")
        await ctx.reply(result_str)

    @commands.command(help="Destroys a group that you've created.",
                      aliases=['gentfernen'])
    async def gdestroy(self, ctx, group_prefix: str = commands.parameter(description="Your group (short name)")):
        group_name = sanitize_group_name(group_prefix, ctx.author)
        await self.delete_group(ctx, group_name)

    @commands.command(help="Purges a group.",
                      aliases=['gbereinigen'],
                      hidden=True)
    @commands.has_permissions(administrator=True)
    async def gpurge(self, ctx, group_name: str = commands.parameter(description="Group (full name)")):
        await self.delete_group(ctx, group_name)

    @commands.command(help="Sets a group key.",
                      aliases=['gsetze'])
    async def gset(self, ctx, group_prefix: str = commands.parameter(description="Your group (without username)"),
                   key: str = commands.parameter(
                       description=f"Key to set. For example: {organize_group.DATE},{organize_group.DESCRIPTION} or "
                                   f"{organize_group.PLAYER_NUMBER}"),
                   value: str = commands.parameter(
                       description="Value to set the key to")):
        group = sanitize_group_name(group_prefix, ctx.author)
        result_str = organize_group.set_key(sanitize_single(ctx.guild), group, key, value)
        await ctx.reply(result_str)

    @commands.command(
        help="Sets date.",
        aliases=['gsetzedatum'])
    async def gsetdate(self, ctx, group_prefix: str = commands.parameter(description="Your group (without username)"),
                       value: str = commands.parameter(
                           description="New date")):
        group = sanitize_group_name(group_prefix, ctx.author)
        result_str = organize_group.set_key(sanitize_single(ctx.guild), group, organize_group.DATE, value)
        await ctx.reply(result_str)

    @commands.command(
        help="Sets description.",
        aliases=['gsetzebeschreibung'])
    async def gsetdescription(self, ctx, group_prefix: str = commands.parameter(description="Your group (short name)"),
                              value: str = commands.parameter(
                                  description="New description")):
        group = sanitize_group_name(group_prefix, ctx.author)
        result_str = organize_group.set_key(sanitize_single(ctx.guild), group, organize_group.DESCRIPTION, value)
        await ctx.reply(result_str)

    @commands.command(
        help="Sets maximum_players number.",
        aliases=['gsetzespieleranzahl'])
    async def gsetnumberofplayers(self, ctx,
                                  group_prefix: str = commands.parameter(description="Your group (short name)"),
                                  value: str = commands.parameter(
                                      description="New number of players")):
        group = sanitize_group_name(group_prefix, ctx.author)
        result_str = organize_group.set_key(sanitize_single(ctx.guild), group, organize_group.PLAYER_NUMBER, value)
        await ctx.reply(result_str)

    @commands.command(help="Removes a player from your group", aliases=['gkick'])
    async def gremove(self, ctx, group_prefix: str = commands.parameter(description="Your goup (short name)."),
                      player: discord.Member = commands.parameter(description="Player to remove.")):
        group = sanitize_group_name(group_prefix, ctx.author)
        status, result_str = organize_group.remove_player(sanitize_single(ctx.guild), group, player.id)

        if status:
            group_role = get(ctx.guild.roles, name=group)
            # removing group role when existing
            if group_role in player.roles:
                await player.remove_roles(group_role)
                logging.debug(f"Removed role {group_role} from user {player}.")
            text_channel = ctx.guild.get_channel(organize_group.get_main_channel(sanitize_single(ctx.guild), group))
            await text_channel.send(f"Verabschiedet <@{player.id}>.")

        await ctx.reply(result_str)

    @commands.command(help="Join a group as a player", aliases=['gbeitreten'])
    async def gjoin(self, ctx, group: str = commands.parameter(description="Group you will join.")):
        group = re.sub('[^0-9a-zA-Z\-_]+', '', group.replace(" ", "-")).lower()

        if False and organize_group.is_owner(sanitize_single(ctx.guild), group, ctx.author.id):
            status, result_str = False, "You can't join your own group."
        else:
            status, result_str = organize_group.add_self(sanitize_single(ctx.guild), group, ctx.author.id)

        if status:
            # get the role by group name
            group_role = get(ctx.guild.roles, name=group)
            await ctx.author.add_roles(group_role)
            logging.debug(f"Added role {group_role} to user {ctx.author}.")
            text_channel = ctx.guild.get_channel(organize_group.get_main_channel(sanitize_single(ctx.guild), group))
            await text_channel.send(
                f"Begrüßt <@{ctx.author.id}>!")

        await ctx.reply(result_str)

    @commands.command(help="Leave a group as a maximum_players", aliases=['gaustreten'])
    async def gleave(self, ctx, group: str = commands.parameter(description="Group you will leave.")):
        group = re.sub('[^0-9a-zA-Z\-_]+', '', group.replace(" ", "-")).lower()
        status, result_str = organize_group.remove_self(sanitize_single(ctx.guild), group, ctx.author.id)

        if status:
            group_role = get(ctx.guild.roles, name=group)
            # removing group role when existing
            user_roles = ctx.author.roles
            if group_role in user_roles:  # only remove if role really exists
                await ctx.author.remove_roles(group_role)
                logging.debug(f"Removed role {group_role} from user {ctx.author}.")
            text_channel = ctx.guild.get_channel(organize_group.get_main_channel(sanitize_single(ctx.guild), group))
            await text_channel.send(f"Verabschiedet <@{ctx.author.id}>.")

        await ctx.reply(result_str)

    @commands.command(help="Added einen Channel zu einer Gruppe.",
                      aliases=['gchannelhinzufügen'])
    async def gaddchannel(self, ctx, group_prefix: str = commands.parameter(description="Your group (short name)"),
                          channel_name: str = commands.parameter(description="Channel name to create"),
                          is_voice: bool = commands.parameter(default=False,
                                                              description="If True, a voice channel is created. Else a text channel.")):
        group_name = sanitize_group_name(group_prefix, ctx.author)
        sanitized_guild = sanitize_single(ctx.guild)
        category = discord.utils.get(ctx.guild.categories, name=group_name)

        # Handle Roles
        everyone = ctx.guild.default_role
        role = discord.utils.get(ctx.guild.roles, name=group_name)
        overwrites = {everyone: discord.PermissionOverwrite(read_messages=False),
                      role: discord.PermissionOverwrite(read_messages=True)}

        # Add Channel
        if is_voice:
            voice_channel = await ctx.guild.create_voice_channel(name=channel_name, overwrites=overwrites,
                                                                 category=category)
            organize_group.add_channel(sanitized_guild, group_name, voice_channel.id)
            logging.debug(f"Created voice channel {voice_channel}")
            await ctx.reply("Created voice channel!")
        else:
            text_channel = await ctx.guild.create_text_channel(name=channel_name, overwrites=overwrites,
                                                               category=category)
            organize_group.add_channel(sanitized_guild, group_name, text_channel.id)
            logging.debug(f"Created text channel {text_channel}")
            await ctx.reply("Created text channel!")
