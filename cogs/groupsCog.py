#!/usr/bin/env python3
import logging

import discord
from discord.ext import commands
from discord.utils import get

from cogs.group import organize_group


def sanitize_group_name(group_prefix, author):
    group_name = f"{group_prefix}_{author}"
    return group_name.replace("#", "").lower()


class GroupCommands(commands.Cog):
    """
    Commands for handling groups
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Creates a new group with yourself as the GM", aliases=['gneu'])
    async def gcreate(self, ctx, group: str = commands.parameter(description="Your group to create"),
                      time: str = commands.parameter(
                          description="Time to play in GMT+1 (for example '25.02.23 14:00')"),
                      player: int = commands.parameter(
                          default=4, description="Maximum number of players"),
                      description: str = commands.parameter(default="Eine spannende Ilaris Runde!",
                                                            description="Description for your soon-to-be players")):
        group_name = sanitize_group_name(group, ctx.author)
        status, result_str = organize_group.create_group(
            group_name, time, player, description)
        everyone = ctx.guild.default_role

        if status:
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
            # create channels
            text_channel = await ctx.guild.create_text_channel(name=group_name, overwrites=overwrites,
                                                               category=category)
            logging.debug(f"Created text channel {text_channel}")
            voice_channel = await ctx.guild.create_voice_channel(name=group_name,
                                                                 overwrites=overwrites,
                                                                 category=category)

            await text_channel.send(f"Hey, <@{ctx.author.id}>! Ich habe dir und deiner Gruppe diesen Kanal erstellt.")
            logging.debug(f"Created voice channel {voice_channel}")
        await ctx.send(result_str)

    @commands.command(help="List all groups", aliases=['gliste'])
    async def glist(self, ctx,
                    full: bool = commands.parameter(default=False, description="'True' to show full groups, too")):
        result_str = organize_group.list_groups(full)
        await ctx.send(result_str)

    @commands.command(help="Destroys a group that you've created", aliases=['gentfernen'])
    async def gdestroy(self, ctx, group_prefix: str = commands.parameter(description="Your group (short name)")):
        group_name = sanitize_group_name(group_prefix, ctx.author)
        status, result_str = organize_group.destroy_group(group_name)
        # if status, delete channels and role
        status = True
        if status:
            # remove role
            role = discord.utils.get(ctx.guild.roles, name=group_name)
            if role:
                await role.delete()
                logging.debug(f"Deleted role {role}.")

            # remove category
            category = discord.utils.get(ctx.guild.categories, name=group_name)
            if category:
                await category.delete()
                logging.debug(f"Deleted category {category}.")
            # remove channels
            for channel in ctx.guild.channels:
                if str(channel) == group_name:
                    await channel.delete()
                    logging.debug(f"Deleted channel {channel}.")

        await ctx.send(result_str)

    @commands.command(
        help="Sets a group key like 'uhrzeit'. Setting 'spielerzahl' below the current number will not remove any "
             "players.",
        aliases=['gsetze'])
    async def gset(self, ctx, group_prefix: str = commands.parameter(description="Your group (short name)"),
                   key: str = commands.parameter(
                       description="Key to set (for example 'uhrzeit')"),
                   value: str = commands.parameter(
                       description="Value to store under key (for example '25.02.23 14:00')")):
        group = sanitize_group_name(group_prefix, ctx.author)
        result_str = organize_group.set_key(group, key, value)
        await ctx.send(result_str)

    @commands.command(
        help="Sets date.",
        aliases=['gsetzedatum'])
    async def gsetdate(self, ctx, group_prefix: str = commands.parameter(description="Your group (short name)"),
                       value: str = commands.parameter(
                           description="New date")):
        group = sanitize_group_name(group_prefix, ctx.author)
        result_str = organize_group.set_key(group, "uhrzeit", value)
        await ctx.send(result_str)

    @commands.command(
        help="Sets description.",
        aliases=['gsetzebeschreibung'])
    async def gsetdescription(self, ctx, group_prefix: str = commands.parameter(description="Your group (short name)"),
                              value: str = commands.parameter(
                                  description="New description")):
        group = sanitize_group_name(group_prefix, ctx.author)
        result_str = organize_group.set_key(group, "beschreibung", value)
        await ctx.send(result_str)

    @commands.command(
        help="Sets player number.",
        aliases=['gsetzespieleranzahl'])
    async def gsetnumberofplayers(self, ctx,
                                  group_prefix: str = commands.parameter(description="Your group (short name)"),
                                  value: str = commands.parameter(
                                      description="New number of players")):
        group = sanitize_group_name(group_prefix, ctx.author)
        result_str = organize_group.set_key(group, "spielerzahl", value)
        await ctx.send(result_str)

    @commands.command(help="Removes a player from your group", aliases=['gkick'])
    async def gremove(self, ctx, group_prefix: str = commands.parameter(description="Your goup (short name)."),
                      player: discord.Member = commands.parameter(description="Player to remove.")):
        group = sanitize_group_name(group_prefix, ctx.author)
        status, result_str = organize_group.remove_player(group, player)

        if status:
            name, discriminator = player.split("#")
            user = discord.utils.get(ctx.guild.members, name=name, discriminator=discriminator)
            group_role = get(ctx.guild.roles, name=group)
            # removing group role when existing
            if group_role in user.roles:
                await user.remove_roles(group_role)
                logging.debug(f"Removed role {group_role} from user {user}.")
            text_channel = discord.utils.get(ctx.guild.text_channels, name=group)
            await text_channel.send(f"Verabschiedet <@{player.id}>.")

        await ctx.send(result_str)

    @commands.command(help="Join a group as a player", aliases=['gbeitreten'])
    async def gjoin(self, ctx, group: str = commands.parameter(description="Group you will join.")):
        group = group.replace("#", "").lower()

        if group.endswith(str(ctx.author).replace("#","").lower()):
            status, result_str = False, "You can't join your own group."
        else:
            status, result_str = organize_group.add_self(group, str(ctx.author))

        if status:
            # get the role by group name
            group_role = get(ctx.guild.roles, name=group)
            await ctx.author.add_roles(group_role)
            logging.debug(f"Added role {group_role} to user {ctx.author}.")
            text_channel = discord.utils.get(ctx.guild.text_channels, name=group)
            await text_channel.send(f"Begr????t <@{ctx.author.id}>!")

        await ctx.send(result_str)

    @commands.command(help="Leave a group as a player", aliases=['gaustreten'])
    async def gleave(self, ctx, group: str = commands.parameter(description="Group you will leave.")):
        group = group.replace("#", "").lower()
        status, result_str = organize_group.remove_self(group, str(ctx.author))

        if status:
            group_role = get(ctx.guild.roles, name=group)
            # removing group role when existing
            user_roles = ctx.author.roles
            if group_role in user_roles:  # only remove if role really exists
                await ctx.author.remove_roles(group_role)
                logging.debug(f"Removed role {group_role} from user {ctx.author}.")
            text_channel = discord.utils.get(ctx.guild.text_channels, name=group)
            await text_channel.send(f"Verabschiedet <@{ctx.author.id}>.")

        await ctx.send(result_str)
