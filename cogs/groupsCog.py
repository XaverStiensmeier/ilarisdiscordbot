#!/usr/bin/env python3
import discord
from discord.ext import commands
from discord.utils import get
from cogs.group import organize_group


class GroupCommands(commands.Cog):
    """
    Commands for handling groups
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Creates a new group with yourself as the GM")
    async def gcreate(self, ctx, group: str = commands.parameter(description="Your group to create"),
                      time: str = commands.parameter(
                          description="Time to play in GMT+1 (for example '25.02.23 14:00')"),
                      player: int = commands.parameter(
                          default=4, description="Maximum number of players"),
                      description: str = commands.parameter(default="Eine spannende Ilaris Runde!",
                                                            description="Description for your soon-to-be players")):
        group_name = f"{group}_{ctx.author}"
        exit_status, result_str = organize_group.create_group(
            group_name, time, player, description)
        everyone = ctx.guild.default_role

        if exit_status:
            # create role
            role = await ctx.guild.create_role(name=group_name)
            # add role to GM
            await ctx.author.add_roles(role)
            # permissions
            overwrites = {everyone: discord.PermissionOverwrite(read_messages=False),
                          role: discord.PermissionOverwrite(read_messages=True)}
            # create category
            category = await ctx.guild.create_category(name=group_name)
            # create channels
            await ctx.guild.create_text_channel(name=group_name, overwrites=overwrites, category=category)
            await ctx.guild.create_voice_channel(name=group_name, overwrites=overwrites, category=category)
        await ctx.send(result_str)

    @commands.command(help="List all groups")
    async def glist(self, ctx,
                    full: bool = commands.parameter(default=False, description="'True' to show full groups, too")):
        result_str = organize_group.list_groups(full)
        await ctx.send(result_str)

    @commands.command(help="Destroys a group that you've created")
    async def gdestroy(self, ctx, group_prefix: str = commands.parameter(description="Your group (short name)")):
        group_name = f"{group_prefix}_{ctx.author}"
        exit_status, result_str = organize_group.destroy_group(group_name)
        # if exit_status, delete channels and role
        await ctx.send(result_str)

    @commands.command(
        help="Sets a group key like 'uhrzeit'. Setting 'spieler' below the current number will not remove any players.")
    async def gset(self, ctx, group_prefix: str = commands.parameter(description="Your group (short name)"),
                   key: str = commands.parameter(
                       description="Key to set (for example 'uhrzeit')"),
                   value: str = commands.parameter(
                       description="Value to store under key (for example '25.02.23 14:00')")):
        group = f"{group_prefix}_{ctx.author}"
        result_str = organize_group.set_key(group, key, value)
        await ctx.send(result_str)

    @commands.command(help="Removes a player from your group")
    async def remove_player(self, ctx, group_prefix: str = commands.parameter(description="Your goup (short name)."),
                            player: str = commands.parameter(description="Player to remove.")):
        group = f"{group_prefix}_{ctx.author}"
        result_str = organize_group.remove_player(group, player)
        await ctx.send(result_str)

    @commands.command(help="Join a group as a player")
    async def gjoin(self, ctx, group: str = commands.parameter(description="Group you will join.")):
        result_str = organize_group.add_self(group, ctx.author)
        await ctx.send(result_str)

    @commands.command(help="Leave a group as a player")
    async def gleave(self, ctx, group: str = commands.parameter(description="Group you will leave.")):

        group_role = get(ctx.guild.roles, name=group)

        # removing group role when existing
        user_roles = ctx.author.roles
        if group_role in user_roles:
            await ctx.author.remove_roles(group_role)

        result_str = organize_group.remove_self(group, ctx.author)
        await ctx.send(result_str)
