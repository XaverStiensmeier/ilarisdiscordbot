#!/usr/bin/env python3
"""
I would like to turn this completly into a Group (and maybe GroupManager) class.
Most of the methods can probably turned into methods very simpple and makes it a lot
easier to use and maintain. Views and Modals could also be generated from a group class
instead of having their own classes. Read more: #75
"""
import signal
import sys
import os
import logging
import yaml
import discord
import asyncio
from filelock import FileLock
from dataclasses import dataclass
from dataclasses import InitVar, field
from typing import Union, List
from discord import abc  # discords base classes
from discord import (CategoryChannel, Interaction, Guild, Role, PermissionOverwrite,
    Interaction, ButtonStyle, User, Member, Client, TextChannel, Message)
from discord.ui import TextInput, button
from discord.ext.commands import Context

from utility.sanitizer import sanitize
from config import DATA
from config import messages as msg
from views.base import BaseModal, BaseView
from cogs.group import organize_group as og
from utility.sanitizer import sanitize
from config import messages as msg
from functools import wraps

# module level functions and variables (cache).

# root level of the file are server, we could also save server specific data in the same
# file, so I renamed it to guilds.yml.
data_file = DATA/"guilds.yml"


def write_yaml():
    with open(data_file, "w+") as file:
        with FileLock("groups.yml.lock"):
            yaml.safe_dump(guilds, file)


def save_yaml(original_function):
    """Decorator to save yaml file after function call.
    after a function decorated with this, the guilds dict is written to yaml file.
    The wrapper works for both async and sync functions.
    """

    @wraps(original_function)
    def wrapper(*args, **kwargs):
        result = original_function(*args, **kwargs)
        write_yaml()
        return result

    @wraps(original_function)
    async def async_wrapper(*args, **kwargs):
        result = await original_function(*args, **kwargs)
        write_yaml()
        return result
    if asyncio.iscoroutinefunction(original_function):
        return async_wrapper
    else:
        return wrapper


@save_yaml
def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)

signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)

# LOAD GROUPS
guilds = {}
if os.path.isfile(data_file):
    with open(data_file, "r") as yaml_file:
        guilds = yaml.safe_load(yaml_file) or {}
else:
    logging.warning("No guilds file found. Trying to create one next save.")


def get_id(object):
    """utility function to get id from discord object or string"""
    if object is None:
        return object
    if isinstance(object, str) or isinstance(object, int):
        return int(object)
    return object.id


@dataclass
class Group:
    """ This class makes all group data and ui elements easy accessible and provides
    convenient methods to interact with the group. It's primarily used from within group
    commands and views. Most attributes of this class directly map to their dictionary repr or json strings 
    and are validated on the fly thanks to @dataclass: 
    https://docs.python.org/3/library/dataclasses.html
    However, some methods require some context (who called it, in which guild etc..) 
    this context (or interaction) is processed in the post_init method, thats called
    after the actual init, generated from @dataclass. Methods use ids of discord objects
    when possible to avoid unnecessary calls to discord API. The methods that require 
    such calls are usually async (i.e. setup_roles, create_channels).
    # TODO: Add some tests

    Dataclass: https://docs.python.org/3/library/dataclasses.html
    The decorator adds some default methods like __init__, __repr__ and allows
    serialization to dict and json. All class variables below can be used as kw_args
    in the constructor.. for example `my_group = Group(name="My Name", ctx=ctx)` will
    create an instance where guild .
    """
    # context (initvars will be skipped in serialization)
    inter: InitVar[Interaction] = None
    ctx: InitVar[Context] = None
    member: InitVar[abc.User] = None
    bot: InitVar[discord.Client] = None  # required to create roles/channels
    # serialized (standard dataclass fields)
    name: str = None
    guild: int = None
    owner: int = None
    date: str = ""
    description: str = ""
    max_players: int = 4
    category: int = None
    role: int = None
    players: list = field(default_factory=list) 
    channel: int = None  # default channel
    # static
    guilds: InitVar[dict] = guilds  # reference to the global guilds dict (??)

    def __post_init__(self, inter, ctx, member, bot: discord.Client, guilds):
        """Post init function to set context and user from initvars."""
        self.guilds = guilds
        self.slug = sanitize(self.name)
        if inter:
            self.inter = inter
            self.member = inter.user
            self.guild = inter.guild.id
            self.bot = inter.bot
        elif ctx:
            self.ctx = ctx
            self.member = ctx.author
            self.guild = ctx.guild.id
            self.bot = ctx.bot
        else:
            if member:
                self.member = member
            if bot:
                self.bot = bot

    @classmethod
    def load(cls, name, ctx=None, inter=None, guild_id=None, create=False):
        """Loads a group object from the guilds dict.
        @param create: if True, a new (unsaved) group object is created for missing data
        @param ctx: set user, guild and bot from context
        @param inter: set user, guild and bot from interaction
        @param guild_id: guild id, required if ctx or inter is not set
        """
        if not guild_id:
            guild_id = ctx.guild.id if ctx else inter.guild.id
        slug = sanitize(name)
        print(slug, guild_id)
        data = guilds.get(guild_id, {}).get(slug)
        if "slug" in data:
            data.pop('slug')  # do we want slug as part of dict/field or just key?
        if not data:
            if create:
                return cls(name=name, ctx=ctx, inter=inter, guild=guild_id)
            raise ValueError(f"Group {name} not found in guild {guild_id}.")
        return cls(**data, ctx=ctx, inter=inter)

    @classmethod
    def groups_from_guild(cls, guild_id: int):
        """Returns all groups from a guild."""
        groups_data = guilds.get(guild_id, {})
        groups = [Group(**data) for data in groups_data.values()]
        return groups

    async def setup_role(self):
        guild = self.bot.get_guild(self.guild)
        if not self.role:
            role = await guild.create_role(name=self.name)
            self.role = role.id
        else:
            role = self.ctx.guild.get_role(self.role)
        if self.ctx:
            await self.ctx.author.add_roles(role)
        elif self.inter:
            await self.inter.user.add_roles(role)
        for p in self.players:
            await guild.get_member(p).add_roles(role)
    
    async def create_channels(self, welcome=True):
        """Creates channels for the group.
        """
        guild: discord.Guild = self.bot.get_guild(self.guild)  # get guild object from id
        if not guild or not self.role:
            raise ValueError("Guild and role are required to setup channels.")
        permissions = {
            guild.default_role: PermissionOverwrite(read_messages=False),
            guild.get_role(self.role): PermissionOverwrite(read_messages=True),
            guild.get_member(self.owner): PermissionOverwrite(
                read_messages=True,
                manage_channels=True,
                manage_messages=True,
                mute_members=True,
                manage_nicknames=True)}
        category = await guild.create_category(name=self.name, overwrites=permissions)
        logging.error("Created category: %s", category.id)
        self.category = category.id  # save category id
        text = await guild.create_text_channel(name="Text", 
            overwrites=permissions, category=category)
        self.default_channel = text.id  # maybe set one channel as the one the bot uses?
        await guild.create_voice_channel(
            name="Voice", overwrites=permissions, category=category)
        if welcome:
            await text.send(msg["gcreate_channel_created"].format(
                author=self.user.id))

    async def setup_guild(self):
        """Creates and assignes roles/channels permissions for this group."""
        await self.setup_role()
        await self.create_channels()

    def __str__(self):
        """String representation of a group. str(group), print(group)..."""
        return f"{self.name} ({self.owner})"
    
    @property
    def info_message(self):
        """message content for !ginfo and the like"""
        return msg["group_info"].format(group=self)
    
    def info_view(self, user: abc.User=None):
        """Returns buttons for group details for this group.
        @param user: user object, required if no ctx or inter is set.
        """
        user = user if user else self.user
        if not user:
            raise ValueError("User is required to create a group view.")
        return GroupView(user)
    
    def as_dict(self):
        """convert object into dict (trivial rn, but could be extended later)"""
        return {
            "name": self.name,
            # "slug": self.slug,
            "owner": self.owner,
            "guild": self.guild,
            "category": self.category,
            "date": self.date, 
            "role": self.role,
            "max_players": self.max_players,
            "description": self.description,
            "players": self.players,
        }
    
    @save_yaml
    def save(self):
        """Saves the group object to the guilds dict."""
        if not self.slug or not self.guild:
            raise ValueError("Group needs a guild and a slug to be saved.")
        guilds.setdefault(self.guild, {})
        guilds[get_id(self.guild)][self.slug] = self.as_dict()
    
    @save_yaml
    def remove_player(self, player: Union[abc.User, int], check_owner=True):
        """Removes a player from the group."""
        player_id = get_id(player)
        if check_owner and not self.is_owner(player_id):
            return False, msg["not_owner"]
        if player_id in self.players:
            self.players.remove(player_id)
            return True, f"Spieler <@{player_id}> wurde entfernt."
        return False, f"Spieler <@{player_id}> ist nicht in Gruppe {self.name}."
    
    async def remove_channels(self):
        """Removes all channels of the group.
        NOTE: as this function is used to be called from destroy, it is not wrapped
        by save_yaml. If you call it directly you can follow it by group.save().
        """
        guild = self.bot.get_guild(self.guild)
        category = guild.get_channel(self.category)
        if not category:
            logging.error(f"Category {self.category} not found in {guilds[self.guild]}")
            return
        for channel in category.channels:
            if channel:
                await channel.delete()
                logging.error(f"Deleted channel {channel.name}.")
        await category.delete()
        logging.error(f"Deleted category {category}.")
    
    @save_yaml
    def rename(self, new_name):
        """Renames the group and updates the slug.
        TODO: change category name and role name as well.
        TODO: allow renaming that ends up in the same slug?
        """
        logging.debug(f"Renaming group {self.name} to {new_name}.")
        old_slug = sanitize(self.name)
        new_slug = sanitize(new_name)
        if old_slug == new_slug:
            self.name = new_name
            return True, msg["group_renamed"].format(group=self)
        if new_slug in guilds.get(self.guild, {}):
            return False, msg["group_exists"]
        if old_slug not in guilds.get(self.guild, {}):
            return False, msg["group_not_found"]
        self.name = new_name
        guilds[self.guild][new_slug] = guilds[self.guild].pop(old_slug)
            
    @save_yaml
    async def destroy(self, user: Union[abc.User, int], cleanup=True, notify=True):
        """Removes the group and all its data from database.
        @param user: user object or id of the user who wants to destroy the group
        @param cleanup: if True, channels and roles are removed as well
        @param notify: send message to all players, that their group is deleted
        @return: tuple(bool, str) status, message
        """
        if not self.is_owner(user):  # TODO: or admin
            return False, msg["not_owner"]
        if not self.exists:
            return False, msg["group_not_found"]
        guild = get_id(self.guild)
        group_data = guilds.get(guild, {}).pop(self.slug)
        if cleanup:
            # remove role
            guild = self.bot.get_guild(self.guild)
            role = guild.get_role(self.role)
            # or discord.utils.get(self.guild.roles, name=self.name)
            if role:
                await role.delete()
                logging.debug(f"Deleted role {role}.")
            # remove channels (category)
            await self.remove_channels()
        if notify:
            for player_id in self.players:
                member = guild.get_member(player_id)
                await member.send(msg["group_deleted_info"].format(author=user, group=self))
        return True, msg["gdestroy_info"].format(group=self)

    def is_owner(self, user: Union[abc.User, int]):
        return get_id(self.owner) == get_id(user)
    
    @property
    def player_count(self):
        return len(self.players)
    
    @property
    def user(self):
        """this does return command author or button clicker, not the owner"""
        if self.ctx:
            return self.ctx.author
        elif self.inter:
            return self.inter.user
        return None
    
    @property
    def exists(self):
        return self.slug in guilds.get(self.guild, {})


class GroupModal(BaseModal, title="Neue Gruppe"):
    """ Modal for creating or editing a group
    This popup can only be created from an interaction (i.e. button click or /command),
    but not from simple !commands. The fields can be set as class variables and the user
    input will be accessible from the instance as self.<field_name>.value.
    We init the form with a group object and modify default values to fake an edit mode.
    NOTE: When the name changes, the slug changes too. -> Two objects in case of rename.
    """
    # this will be added to each instance (self.name...) from parent.
    name = TextInput(label=msg["name_la"], placeholder=msg["name_ph"], min_length=1, max_length=80)
    text = TextInput(label=msg["text_la"], placeholder=msg["text_ph"], required=False, max_length=1400, min_length=0, style=discord.TextStyle.long)
    max_players = TextInput(label=msg["slots_la"], placeholder=msg["slots_ph"], required=False, min_length=0, max_length=1, default=4)
    date = TextInput(label=msg["date_la"], placeholder=msg["date_ph"], required=False, min_length=0, max_length=150)

    def __init__(self, group=None):
        self.group = group
        defaults = group.as_dict() if group else {
            "name": "", "text": "", "max_players": 4, "date": ""}
        super().__init__(timeout=460.0)
        # modify defaults when editing an existing group
        self.name.default = group.name
        self.text.default = group.description
        self.max_players.default = group.max_players
        self.date.default = group.date

    async def on_submit(self, inter: Interaction) -> None:
        # await super().on_submit(interaction)
        # on name change the key of the dict is required to change (bad practise?)
        if self.group is not None and self.name.value != self.group.name:
            print("Name changed, creating new slug/key.")
            group = Group.load(self.group.name, inter=inter, create=True)
            group.rename(self.name.value)
        group = Group(  # create object from form input
            name=self.name.value,
            description=self.text.value,
            max_players=int(self.max_players.value),
            date=self.date.value,
            inter=inter,
            bot=self.bot
        )
        group.save()  # write to yaml
        await group.setup_guild()  # channels and roles etc..
        await inter.response.send_message(msg["submit_success"], ephemeral=True)


class GroupView(BaseView):
    """ Group detail View
    This is a placeholder for now. A view is can be attached to a message and contains
    interactive elements like buttons or select menus. Creating a class like this might 
    help to quickly create messages with group details and options to interact with them.
    """
    interaction = None
    message = None
    group = None  # for now sanitized name, turns into group object later
    
    @button(label=msg["btn_join"], emoji="🍻", style=ButtonStyle.green)
    async def join(self, inter: Interaction, button) -> None:
        if self.group is None:
            status, answer = False, msg["no_group_set"]
        else:
            status, answer = og.add_self(
                sanitize(inter.guild.name),
                sanitize(self.group),
                inter.user.id)
        # ephemeral: only the interacting user sees the response.
        await inter.response.send_message(answer, ephemeral=True)


class NewGroupView(BaseView):
    """ View for !gcreate command
    NOTE: not yet implemented.. try with !view. Maybe we can reuse the group_modal
    """

    @discord.ui.button(label="Gruppe erstellen", style=discord.ButtonStyle.green)
    async def new(self, inter, button) -> None:
        group_form = GroupModal()
        group_form.bot = self.bot
        await inter.response.send_modal(group_form)


class GroupAdminView(BaseView):
    """Buttons for group admin commands like edit, delete, announce, etc.
    """

    @discord.ui.button(label=msg["btn_edit"], style=discord.ButtonStyle.blurple)
    async def edit(self, inter, button) -> None:
        group_form = GroupModal()
        group_form.name = self.name
        group_form.text = self.text
        group_form.max_players = self.max_players
        group_form.date = self.date
        group_form.edit = True
        await inter.response.send_modal(group_form)

    @button(label=msg["btn_edit"], emoji="✏️", style=ButtonStyle.blurple)
    async def edit(self, inter, button) -> None:
        """ open modal to edit group on button click
        TODO: not fully implemented yet, modal is just an example (not saving)
        """
        # group_form = GroupModal()
        # await inter.response.send_modal(group_form)
        print(inter.name)
        # await inter.response.edit_message("Noch nicht implementiert", view=self)

    @button(label=msg["btn_destroy"], emoji="🗑️", style=ButtonStyle.red)
    async def destroy(self, inter, button) -> None:
        """ destroy a group from button click
        TODO: check permissions, maybe confirm dialog?
        """
        guild = sanitize(inter.guild.name)
        if not og.is_owner(guild, self.group, inter.user.id):
            await inter.response.send_message(msg["not_owner"], ephemeral=True)
            return
        status, answer = og.destroy_group(guild, self.group, inter.user.id)[:2]
        await inter.response.send_message(answer, ephemeral=True)

