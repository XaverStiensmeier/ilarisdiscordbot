#!/usr/bin/env python3
import logging
import re

import discord
from discord.ext import commands
from discord.ext.commands import Context, Bot, param, Cog, command
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
            # raise commands.CommandInvokeError(error)  # prevent propagation

    @command(help=msg["glist_help"], aliases=['gliste'])
    async def glist(self, ctx, full: bool = param(
            default=False, description=msg["glist_desc"])
        ):
        await ctx.reply(msg["glist_header"])
        for group in Group.groups_from_guild(ctx.guild.id):
            group.message = await ctx.reply(
                group.info_message, view=group.info_view(ctx.author))

    @command(help=msg["gedit_help"], aliases=['gbearbeiten'])
    async def gedit(self, ctx,
        group_name: str=param(description=msg["gedit_group_param"]),
        key: str=param(description=msg["gedit_key_param"]),
        value: str=param(description=msg["gedit_val_param"]),
    ):
        try:
            group = Group.load(group_name, ctx=ctx)
        except ValueError as e:
            await ctx.reply(str(e))
            return
        if not group.is_owner(ctx.author.id):  # TODO: or admin
            await ctx.reply(msg["not_owner"])
            return
        if not key in ["name", "date", "description", "max_players"]:
            await ctx.reply(msg["gedit_key_error"])
            return
        if key == "max_players":
            value = int(value)
        setattr(group, key, value)
        group.save()
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

    @command(
        help=msg["gsetdate_help"],
        aliases=['gsetzedatum'])
    async def gsetdate(self, ctx, 
        group_prefix: str = param(description=msg["group_prefix"]),
        value: str = param(
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
        group: str = param(description=msg["gsetdescription_group"]),
        value: str = param(
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
        group_prefix: str = param(description=msg["group_prefix"]),
    value: str = param(
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
        group: str = param(description=msg["group_prefix"]),
        player: discord.Member = param(description=msg["gremove_player"])
    ):
        group = Group.load(group, ctx=ctx)
        status, result_str = await group.remove_player(player.id)
        await ctx.reply(result_str)

    @command(help=msg["gjoin_help"], aliases=['gbeitreten'])
    async def gjoin(self, ctx, 
        group: str = param(description=msg["gjoin_group"])
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
        group: str = param(
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

    # TODO: if permissions for channels/roles work, than remove this command and messages
    @command(help=msg["gaddchannel_help"],
                      aliases=['gchannelhinzufügen'])
    async def gaddchannel(
        self, ctx, 
        group: str = param(description=msg["group_name"]),
        channel_name: str = param(
            description=msg["gaddchannel_channel"]),
        is_voice: bool = param(
            default=False,
            description=msg["gaddchannel_voice"])
    ):
        """Create a new text or voice channel in the specified group category.
        NOTE: Added permissions for owner to manage category channel.
        Should be able to create channels using discord ui.
        """
        # TODO: only allow for gm or for everyone?
        slug = sanitize(group)
        sanitized_guild = sanitize(ctx.guild.name)
        category = discord.utils.get(ctx.guild.categories, name=group)

        # Handle Roles
        everyone = ctx.guild.default_role
        role = discord.utils.get(ctx.guild.roles, name=group)
        overwrites = {everyone: discord.PermissionOverwrite(read_messages=False),
                      role: discord.PermissionOverwrite(read_messages=True)}

        # Add Channel
        if is_voice:
            voice_channel = await ctx.guild.create_voice_channel(
                name=channel_name, 
                overwrites=overwrites,
                category=category
            )
            og.add_channel(sanitized_guild, slug, voice_channel.id)
            logging.debug(f"Created voice channel {voice_channel}")
            await ctx.reply(msg["gaddchannel_created_voice"])
        else:
            print(category)
            print(overwrites)
            text_channel = await ctx.guild.create_text_channel(
                name=channel_name, 
                overwrites=overwrites,
                category=category
            )
            # og.add_channel(sanitized_guild, slug, text_channel.id)
            # not need. group only tracks category
            logging.debug(f"Created text channel {text_channel}")
            await ctx.reply(msg["gaddchannel_created_text"])

    # TODO: remove and/or make this admin commands only (maybe confirm dialog)
    @command()
    async def removeallchannels(self, ctx):
        for channel in ctx.guild.channels:
            await channel.delete()
    
    @command()
    async def removeallroles(self, ctx):
        for role in ctx.guild.roles:
            try:
                await role.delete()
            except:
                pass
    
    # TODO: should be admin and/or GM command?
    @command()
    async def gadd(self, ctx, group: str, player: discord.Member):
        group = Group.load(group, ctx=ctx)
        await group.add_player(player.id)
        await ctx.reply(f"Added <@{player.id}> to {group.name}")
        
